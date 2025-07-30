"""Tests for the cloud storage service."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from src.whatsapp_image_bot.services.cloud_storage import S3StorageService


@pytest.fixture
def mock_config():
    """Mock configuration with valid AWS credentials."""
    with patch("src.whatsapp_image_bot.services.cloud_storage.app_config") as mock:
        mock.AWS_ACCESS_KEY_ID = "test_access_key"
        mock.AWS_SECRET_ACCESS_KEY = "test_secret_key"
        mock.AWS_REGION = "us-east-1"
        mock.S3_BUCKET_NAME = "test-bucket"
        yield mock


@pytest.fixture
def mock_s3_client():
    """Mock boto3 S3 client."""
    with patch("boto3.client") as mock_client:
        yield mock_client


def test_s3_storage_service_initialization_success(mock_config, mock_s3_client):
    """Tests that S3StorageService initializes correctly with valid config."""
    service = S3StorageService()

    assert service.bucket_name == "test-bucket"
    assert service.region == "us-east-1"
    mock_s3_client.assert_called_once_with(
        "s3",
        aws_access_key_id="test_access_key",
        aws_secret_access_key="test_secret_key",
        region_name="us-east-1",
    )


def test_s3_storage_service_initialization_missing_config():
    """Tests that S3StorageService raises ValueError with missing config."""
    with patch(
        "src.whatsapp_image_bot.services.cloud_storage.app_config"
    ) as mock_config:
        mock_config.AWS_ACCESS_KEY_ID = None
        mock_config.AWS_SECRET_ACCESS_KEY = "test_secret_key"
        mock_config.AWS_REGION = "us-east-1"
        mock_config.S3_BUCKET_NAME = "test-bucket"

        with pytest.raises(
            ValueError, match="AWS S3 credentials and configuration are not fully set"
        ):
            S3StorageService()


def test_upload_file_success(mock_config, mock_s3_client):
    """Tests successful file upload to S3."""
    mock_client_instance = MagicMock()
    mock_s3_client.return_value = mock_client_instance

    service = S3StorageService()
    test_bytes = b"test image data"
    object_name = "processed/test_image.jpg"

    result = service.upload_file(test_bytes, object_name)

    expected_url = (
        "https://test-bucket.s3.us-east-1.amazonaws.com/processed/test_image.jpg"
    )
    assert result == expected_url

    mock_client_instance.upload_fileobj.assert_called_once()
    call_args = mock_client_instance.upload_fileobj.call_args
    assert call_args[0][1] == "test-bucket"  # bucket_name
    assert call_args[0][2] == object_name  # object_name
    assert call_args[1]["ExtraArgs"]["ContentType"] == "image/jpeg"


def test_upload_file_no_credentials_error(mock_config, mock_s3_client):
    """Tests that upload_file handles NoCredentialsError gracefully."""
    mock_client_instance = MagicMock()
    mock_client_instance.upload_fileobj.side_effect = NoCredentialsError()
    mock_s3_client.return_value = mock_client_instance

    service = S3StorageService()
    test_bytes = b"test image data"
    object_name = "processed/test_image.jpg"

    result = service.upload_file(test_bytes, object_name)

    assert result is None


def test_upload_file_client_error(mock_config, mock_s3_client):
    """Tests that upload_file handles ClientError gracefully."""
    mock_client_instance = MagicMock()
    client_error = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
        operation_name="upload_fileobj",
    )
    mock_client_instance.upload_fileobj.side_effect = client_error
    mock_s3_client.return_value = mock_client_instance

    service = S3StorageService()
    test_bytes = b"test image data"
    object_name = "processed/test_image.jpg"

    result = service.upload_file(test_bytes, object_name)

    assert result is None


def test_upload_file_generic_exception(mock_config, mock_s3_client):
    """Tests that upload_file handles generic exceptions gracefully."""
    mock_client_instance = MagicMock()
    mock_client_instance.upload_fileobj.side_effect = RuntimeError("Unexpected error")
    mock_s3_client.return_value = mock_client_instance

    service = S3StorageService()
    test_bytes = b"test image data"
    object_name = "processed/test_image.jpg"

    result = service.upload_file(test_bytes, object_name)

    assert result is None


def test_upload_file_with_different_object_names(mock_config, mock_s3_client):
    """Tests that upload_file works with different object name formats."""
    mock_client_instance = MagicMock()
    mock_s3_client.return_value = mock_client_instance

    service = S3StorageService()
    test_bytes = b"test image data"

    test_cases = [
        "image.jpg",
        "folder/image.jpg",
        "deep/nested/folder/image.jpg",
        "processed/message_123_20240101.jpg",
    ]

    for object_name in test_cases:
        result = service.upload_file(test_bytes, object_name)
        expected_url = f"https://test-bucket.s3.us-east-1.amazonaws.com/{object_name}"
        assert result == expected_url
