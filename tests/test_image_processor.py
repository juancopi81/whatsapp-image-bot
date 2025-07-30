"""Tests for the image processor service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.whatsapp_image_bot.services.image_processor import (
    MediaDownloadError,
    MediaValidationError,
    UploadError,
    process_image,
)


@pytest.fixture
def mock_s3_service():
    """Mock S3 storage service."""
    mock = MagicMock()
    mock.upload_file.return_value = (
        "https://test-bucket.s3.us-east-1.amazonaws.com/processed/test_123_456.jpg"
    )
    return mock


@pytest.fixture
def mock_fal_client():
    """Mock FalClient."""
    mock = AsyncMock()
    mock.stylize_image.return_value = "https://fal.ai/stylized/image.jpg"
    return mock


@pytest.fixture
def mock_download_image():
    """Mock download_image_from_url function."""
    with patch(
        "src.whatsapp_image_bot.services.image_processor.download_image_from_url"
    ) as mock:
        mock.return_value = b"stylized image bytes"
        yield mock


@pytest.mark.asyncio
async def test_process_image_success_public_url(
    mock_s3_service, mock_fal_client, mock_download_image
):
    """Tests successful image processing with a public URL."""
    test_url = "https://example.com/image.jpg"
    message_sid = "test_message_123"

    result = await process_image(
        test_url, message_sid, s3=mock_s3_service, fal_client=mock_fal_client
    )

    assert (
        result
        == "https://test-bucket.s3.us-east-1.amazonaws.com/processed/test_123_456.jpg"
    )

    # Verify the workflow
    mock_fal_client.stylize_image.assert_called_once_with(test_url)
    mock_download_image.assert_called_once_with("https://fal.ai/stylized/image.jpg")
    mock_s3_service.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_process_image_success_twilio_url(
    mock_s3_service, mock_fal_client, mock_download_image
):
    """Tests successful image processing with a Twilio URL."""
    twilio_url = (
        "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test"
    )
    message_sid = "test_message_123"

    # Mock the Twilio media fetch
    mock_response = MagicMock()
    mock_response.content = b"original image bytes"
    mock_response.headers = {"Content-Type": "image/jpeg"}
    mock_response.status_code = 200

    with (
        patch(
            "src.whatsapp_image_bot.services.image_processor.Config"
        ) as mock_config_class,
        patch(
            "src.whatsapp_image_bot.services.image_processor._get_twilio_http_client"
        ) as mock_get_client,
        patch(
            "src.whatsapp_image_bot.services.image_processor._fetch_with_retry"
        ) as mock_fetch,
        patch("asyncio.to_thread") as mock_to_thread,
    ):
        # Setup config
        mock_config = MagicMock()
        mock_config.TWILIO_ACCOUNT_SID = "test_sid"
        mock_config.TWILIO_AUTH_TOKEN = "test_token"
        mock_config_class.return_value = mock_config

        # Setup HTTP client and fetch
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_fetch.return_value = mock_response

        # Mock S3 upload for original image (returns URL for fal.ai input)
        mock_to_thread.side_effect = [
            "https://test-bucket.s3.us-east-1.amazonaws.com/original/test_message_123_456.jpg",  # Original upload
            "https://test-bucket.s3.us-east-1.amazonaws.com/processed/test_message_123_456.jpg",  # Final upload
        ]

        result = await process_image(
            twilio_url, message_sid, s3=mock_s3_service, fal_client=mock_fal_client
        )

        assert (
            result
            == "https://test-bucket.s3.us-east-1.amazonaws.com/processed/test_message_123_456.jpg"
        )

        # Verify Twilio URL was fetched
        mock_fetch.assert_called_once_with(twilio_url, mock_client)

        # Verify fal.ai was called with the re-hosted URL
        mock_fal_client.stylize_image.assert_called_once_with(
            "https://test-bucket.s3.us-east-1.amazonaws.com/original/test_message_123_456.jpg"
        )


@pytest.mark.asyncio
async def test_process_image_twilio_missing_credentials():
    """Tests that processing raises MediaValidationError with missing Twilio credentials."""
    twilio_url = (
        "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test"
    )
    message_sid = "test_message_123"

    with patch(
        "src.whatsapp_image_bot.services.image_processor.Config"
    ) as mock_config_class:
        mock_config = MagicMock()
        mock_config.TWILIO_ACCOUNT_SID = None
        mock_config.TWILIO_AUTH_TOKEN = "test_token"
        mock_config_class.return_value = mock_config

        with pytest.raises(
            MediaValidationError, match="Twilio credentials are not configured"
        ):
            await process_image(twilio_url, message_sid)


@pytest.mark.asyncio
async def test_process_image_twilio_unsupported_media_type():
    """Tests that processing raises MediaValidationError for unsupported media types."""
    twilio_url = (
        "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test"
    )
    message_sid = "test_message_123"

    mock_response = MagicMock()
    mock_response.content = b"video content"
    mock_response.headers = {"Content-Type": "video/mp4"}

    with (
        patch(
            "src.whatsapp_image_bot.services.image_processor.Config"
        ) as mock_config_class,
        patch(
            "src.whatsapp_image_bot.services.image_processor._get_twilio_http_client"
        ) as mock_get_client,
        patch(
            "src.whatsapp_image_bot.services.image_processor._fetch_with_retry"
        ) as mock_fetch,
    ):
        mock_config = MagicMock()
        mock_config.TWILIO_ACCOUNT_SID = "test_sid"
        mock_config.TWILIO_AUTH_TOKEN = "test_token"
        mock_config_class.return_value = mock_config

        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_fetch.return_value = mock_response

        with pytest.raises(MediaValidationError, match="Unsupported media type"):
            await process_image(twilio_url, message_sid)


@pytest.mark.asyncio
async def test_process_image_twilio_size_limit_exceeded():
    """Tests that processing raises MediaValidationError when original image exceeds size limit."""
    twilio_url = (
        "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test"
    )
    message_sid = "test_message_123"

    # Create content larger than MAX_IMAGE_BYTES (5MB)
    large_content = b"x" * (6 * 1024 * 1024)  # 6MB
    mock_response = MagicMock()
    mock_response.content = large_content
    mock_response.headers = {"Content-Type": "image/jpeg"}

    with (
        patch(
            "src.whatsapp_image_bot.services.image_processor.Config"
        ) as mock_config_class,
        patch(
            "src.whatsapp_image_bot.services.image_processor._get_twilio_http_client"
        ) as mock_get_client,
        patch(
            "src.whatsapp_image_bot.services.image_processor._fetch_with_retry"
        ) as mock_fetch,
    ):
        mock_config = MagicMock()
        mock_config.TWILIO_ACCOUNT_SID = "test_sid"
        mock_config.TWILIO_AUTH_TOKEN = "test_token"
        mock_config_class.return_value = mock_config

        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        mock_fetch.return_value = mock_response

        with pytest.raises(
            MediaValidationError, match="Original image exceeds size limit"
        ):
            await process_image(twilio_url, message_sid)


@pytest.mark.asyncio
async def test_process_image_download_failure(mock_s3_service, mock_fal_client):
    """Tests that processing raises MediaDownloadError when download fails."""
    test_url = "https://example.com/image.jpg"
    message_sid = "test_message_123"

    with patch(
        "src.whatsapp_image_bot.services.image_processor.download_image_from_url"
    ) as mock_download:
        mock_download.return_value = None  # Download failed

        with pytest.raises(
            MediaDownloadError, match="No bytes downloaded from stylized URL"
        ):
            await process_image(
                test_url, message_sid, s3=mock_s3_service, fal_client=mock_fal_client
            )


@pytest.mark.asyncio
async def test_process_image_stylized_size_limit_exceeded(
    mock_s3_service, mock_fal_client
):
    """Tests that processing raises MediaValidationError when stylized image exceeds size limit."""
    test_url = "https://example.com/image.jpg"
    message_sid = "test_message_123"

    # Create content larger than MAX_IMAGE_BYTES (5MB)
    large_content = b"x" * (6 * 1024 * 1024)  # 6MB

    with patch(
        "src.whatsapp_image_bot.services.image_processor.download_image_from_url"
    ) as mock_download:
        mock_download.return_value = large_content

        with pytest.raises(
            MediaValidationError, match="Stylized image exceeds size limit"
        ):
            await process_image(
                test_url, message_sid, s3=mock_s3_service, fal_client=mock_fal_client
            )


@pytest.mark.asyncio
async def test_process_image_s3_upload_failure(mock_fal_client, mock_download_image):
    """Tests that processing raises UploadError when S3 upload fails."""
    test_url = "https://example.com/image.jpg"
    message_sid = "test_message_123"

    mock_s3_service = MagicMock()
    mock_s3_service.upload_file.return_value = None  # Upload failed

    with pytest.raises(UploadError, match="Failed to upload image to S3"):
        await process_image(
            test_url, message_sid, s3=mock_s3_service, fal_client=mock_fal_client
        )


@pytest.mark.asyncio
async def test_process_image_fal_client_error(mock_s3_service):
    """Tests that processing propagates FalClient errors."""
    test_url = "https://example.com/image.jpg"
    message_sid = "test_message_123"

    mock_fal_client = AsyncMock()
    mock_fal_client.stylize_image.side_effect = RuntimeError("Fal API error")

    with pytest.raises(RuntimeError, match="Fal API error"):
        await process_image(
            test_url, message_sid, s3=mock_s3_service, fal_client=mock_fal_client
        )


@pytest.mark.asyncio
async def test_process_image_different_file_extensions(
    mock_s3_service, mock_fal_client, mock_download_image
):
    """Tests that process_image handles different file extensions correctly."""
    message_sid = "test_message_123"

    test_cases = [
        ("https://fal.ai/stylized/image.png", ".png"),
        ("https://fal.ai/stylized/image.webp", ".webp"),
        ("https://fal.ai/stylized/image", ".jpg"),  # No extension defaults to .jpg
        (
            "https://fal.ai/stylized/image.txt",
            ".jpg",
        ),  # Unknown extension defaults to .jpg
    ]

    for stylized_url, expected_ext in test_cases:
        mock_fal_client.stylize_image.return_value = stylized_url

        await process_image(
            "https://example.com/original.jpg",
            message_sid,
            s3=mock_s3_service,
            fal_client=mock_fal_client,
        )

        # Check that upload_file was called with correct object name
        call_args = mock_s3_service.upload_file.call_args
        object_name = call_args[1]["object_name"]
        assert object_name.endswith(
            expected_ext
        ), f"Expected {expected_ext} but got {object_name}"
        assert object_name.startswith(f"processed/{message_sid}_")

        # Reset for next iteration
        mock_s3_service.reset_mock()


@pytest.mark.asyncio
async def test_fetch_with_retry_success():
    """Tests _fetch_with_retry with successful response."""
    from src.whatsapp_image_bot.services.image_processor import _fetch_with_retry

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response

    result = await _fetch_with_retry("https://example.com/test", mock_client)

    assert result == mock_response
    mock_client.get.assert_called_once_with("https://example.com/test", timeout=15.0)
    mock_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_with_retry_with_retries():
    """Tests _fetch_with_retry with transient errors and eventual success."""
    from src.whatsapp_image_bot.services.image_processor import _fetch_with_retry

    mock_client = AsyncMock()

    # First two calls return 503, third succeeds
    mock_response_503 = MagicMock()
    mock_response_503.status_code = 503
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200

    mock_client.get.side_effect = [
        mock_response_503,
        mock_response_503,
        mock_response_200,
    ]

    with patch("asyncio.sleep") as mock_sleep:
        result = await _fetch_with_retry("https://example.com/test", mock_client)

    assert result == mock_response_200
    assert mock_client.get.call_count == 3
    assert mock_sleep.call_count == 2  # Two retries
    mock_response_200.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_with_retry_max_retries_exceeded():
    """Tests _fetch_with_retry when max retries are exceeded."""
    from src.whatsapp_image_bot.services.image_processor import _fetch_with_retry

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.RequestError("Connection failed")

    with patch("asyncio.sleep"):
        with pytest.raises(httpx.RequestError, match="Connection failed"):
            await _fetch_with_retry("https://example.com/test", mock_client)

    assert mock_client.get.call_count == 3  # 3 attempts total
