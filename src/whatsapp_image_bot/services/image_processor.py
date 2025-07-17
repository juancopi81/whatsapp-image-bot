"""Image processor service for the WhatsApp Image Stylization Bot.

This module provides the `process_image` function, which is responsible for
processing an image from a URL and uploading it to S3.

The function uses the `FalClient` to stylize the image and the `S3StorageService`
to upload the image to S3.

"""

import asyncio
import os
import time
from urllib.parse import urlparse

from whatsapp_image_bot.clients import FalClient
from whatsapp_image_bot.services import S3StorageService
from whatsapp_image_bot.utils import download_image_from_url, get_logger

logger = get_logger(__name__)
s3_service = S3StorageService()


async def process_image(original_url: str, message_sid: str) -> str:
    """Process an image from a URL and upload it to S3.

    Args:
    ----
        original_url: The URL of the original image.
        message_sid: The SID of the message.

    Returns:
    -------
        The URL of the uploaded image.

    Raises:
    ------
        Exception: If the image is not uploaded to S3.

    """
    try:
        fal_client = FalClient()

        # 1. Stylize the image
        stylized_url = await fal_client.stylize_image(original_url)
        logger.info(f"Stylized image URL: {stylized_url}")

        # 2. Get image bytes from stylized URL
        image_bytes = await download_image_from_url(stylized_url)
        if not image_bytes:
            raise ValueError("No bytes downloaded from stylized URL.")
        logger.info("Image downloaded from stylized URL")

        # 3. Create a unique object name for the image
        ext = os.path.splitext(urlparse(stylized_url).path)[1] or ".jpg"
        object_name = f"processed/{message_sid}_{int(time.time())}{ext}"

        # 4. Upload (run blocking boto3 call in a thread)
        s3_url: str | None = await asyncio.to_thread(
            s3_service.upload_file,
            file_bytes=image_bytes,
            object_name=object_name,
        )

        # If the image is not uploaded, raise an error
        if s3_url is None:
            raise Exception("Failed to upload image to S3.")

        logger.info("Uploaded to S3", extra={"sid": message_sid, "url": s3_url})
        return s3_url

    except Exception:
        logger.exception("Error processing image", extra={"sid": message_sid})
        raise
