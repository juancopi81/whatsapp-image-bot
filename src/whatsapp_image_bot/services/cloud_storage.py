"""Class to manage file uploads to an AWS S3 bucket.

This class provides a service to manage file uploads to an AWS S3 bucket.
"""

from io import BytesIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from whatsapp_image_bot.config import Config
from whatsapp_image_bot.utils import get_logger

# Define public API for this module
__all__ = ["s3_service"]

# App config
app_config = Config()

# Logger
logger = get_logger(__name__)


class S3StorageService:
    """A service to manage file uploads to an AWS S3 bucket."""

    def __init__(self):
        """Initializes the S3 client."""
        # Ensure all required AWS configuration is present
        if not all(
            [
                app_config.AWS_ACCESS_KEY_ID,
                app_config.AWS_SECRET_ACCESS_KEY,
                app_config.AWS_REGION,
                app_config.S3_BUCKET_NAME,
            ]
        ):
            raise ValueError(
                "AWS S3 credentials and configuration are not fully set in the environment."
            )

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=app_config.AWS_REGION,
        )
        self.bucket_name = app_config.S3_BUCKET_NAME
        self.region = app_config.AWS_REGION

    def upload_file(self, file_bytes: bytes, object_name: str) -> str | None:
        """Uploads a file from bytes to the S3 bucket and returns its public URL.

        Args:
        ----
            file_bytes: The bytes of the file to upload.
            object_name: The desired name of the file in the S3 bucket (e.g., "processed/image.jpg").

        Returns:
        -------
            The public URL of the uploaded file, or None if the upload failed.

        """
        try:
            # Use BytesIO to treat the raw bytes as a file-like object
            file_obj = BytesIO(file_bytes)

            # The 'ExtraArgs' are crucial for making the file public
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                ExtraArgs={
                    "ContentType": "image/jpeg",
                },
            )

            # Construct the standard public URL for the object
            public_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_name}"

            logger.info(f"✅ Successfully uploaded {object_name} to {public_url}")
            return public_url

        except NoCredentialsError:
            logger.error("❌ Credentials not available for AWS S3.")
            return None
        except ClientError as e:
            logger.error(f"❌ An S3 client error occurred: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during upload: {e}")
            return None


# Create a single, reusable instance of the service
s3_service = S3StorageService()
