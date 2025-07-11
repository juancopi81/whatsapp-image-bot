"""Tests for the API clients."""

from unittest.mock import AsyncMock, patch

import pytest

from src.whatsapp_image_bot.clients.fal_client import MODEL_ID, FalClient


# This marks the test as an asyncio test for pytest
@pytest.mark.asyncio
async def test_fal_client_stylize_image_success():
    """Tests that FalClient correctly parses a successful API response."""
    # 1. Prepare a fake response that mimics the real fal.ai output
    fake_api_response = {"images": [{"url": "https://fake.url/stylized_image.jpg"}]}

    # 2. Use a "patch" to replace the real fal_client.submit_async
    #    with a mock that returns our fake response.
    patch_target = "src.whatsapp_image_bot.clients.fal_client.fal_client.submit_async"
    with patch(patch_target, new_callable=AsyncMock) as mock_submit:
        # Configure the mock's handler to return our fake data
        mock_handler = AsyncMock()
        mock_handler.get.return_value = fake_api_response
        mock_submit.return_value = mock_handler

        # 3. Run the code we want to test
        client = FalClient()
        test_url = "https://example.com/original.jpg"
        result_url = await client.stylize_image(test_url)

        # 4. Assert that the result is what we expect
        assert result_url == "https://fake.url/stylized_image.jpg"

        # Optional: Assert that our code *would* call submit_async with the correct arguments
        mock_submit.assert_awaited_once_with(
            MODEL_ID,
            arguments={
                "prompt": "Change to Simpsons style while maintaining the original composition and object placement",
                "image_url": test_url,
            },
        )


@pytest.mark.asyncio
async def test_fal_client_stylize_image_no_images():
    """Tests that FalClient raises when the API responds without images."""
    fake_api_response = {"images": []}  # No images returned

    with patch("fal_client.submit_async", new_callable=AsyncMock) as mock_submit:
        mock_handler = AsyncMock()
        mock_handler.get.return_value = fake_api_response
        mock_submit.return_value = mock_handler

        client = FalClient()
        with pytest.raises(Exception, match="no images"):
            await client.stylize_image("https://example.com/original.jpg")


@pytest.mark.asyncio
async def test_fal_client_stylize_image_missing_images_key():
    """Tests that FalClient raises when the 'images' key is missing."""
    fake_api_response = {}  # Completely missing the "images" key
    patch_target = "src.whatsapp_image_bot.clients.fal_client.fal_client.submit_async"
    with patch(patch_target, new_callable=AsyncMock) as mock_submit:
        mock_handler = AsyncMock()
        mock_handler.get.return_value = fake_api_response
        mock_submit.return_value = mock_handler

        client = FalClient()
        with pytest.raises(Exception, match="no images"):
            await client.stylize_image("https://example.com/original.jpg")


@pytest.mark.asyncio
async def test_fal_client_stylize_image_api_error():
    """Tests that FalClient propagates unexpected exceptions from fal_client."""
    with patch(
        "fal_client.submit_async",
        side_effect=RuntimeError("boom"),
    ):
        client = FalClient()
        with pytest.raises(RuntimeError, match="boom"):
            await client.stylize_image("https://example.com/original.jpg")
