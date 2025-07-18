"""Image processor service for the WhatsApp Image Stylization Bot.

This module provides the `process_image` function, which is responsible for
processing an image from a URL and uploading it to S3.

The function uses the `FalClient` to stylize the image and the `S3StorageService`
to upload the image to S3.

"""

import asyncio
import mimetypes
import os
import time
from urllib.parse import urlparse

import httpx

from whatsapp_image_bot.clients.fal_client import FalClient
from whatsapp_image_bot.config import Config
from whatsapp_image_bot.services.cloud_storage import S3StorageService
from whatsapp_image_bot.utils.helpers import download_image_from_url
from whatsapp_image_bot.utils.logger import get_logger

logger = get_logger(__name__)
s3_service = S3StorageService()


async def _ensure_public_url(url: str, message_sid: str, ts: int) -> str:
    """Ensure a URL is publicly accessible.

    If Twilio media URL, returns a new public S3 URL.
    """
    if not url.startswith("https://api.twilio.com"):
        return url

    cfg = Config()
    if not cfg.TWILIO_ACCOUNT_SID or not cfg.TWILIO_AUTH_TOKEN:
        raise ValueError("Twilio credentials are not configured.")

    async with httpx.AsyncClient(
        auth=httpx.BasicAuth(cfg.TWILIO_ACCOUNT_SID, cfg.TWILIO_AUTH_TOKEN),
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    # Upload the original image to S3 so fal.ai can reach it
    # Get the extension from the URL
    ctype = response.headers.get("Content-Type", "") or ""
    base_type = ctype.split(";")[0].strip().lower()

    # Guard image types
    if not base_type.startswith("image/"):
        raise ValueError(f"Unsupported media type: {base_type}")

    # Normalize common JPEG quirk
    if base_type in {"image/jpeg", "image/jpg"}:
        orig_ext = ".jpg"
    else:
        orig_ext = mimetypes.guess_extension(base_type) or ".jpg"
    orig_key = f"original/{message_sid}_{ts}{orig_ext}"
    uploaded_url = await asyncio.to_thread(
        s3_service.upload_file,
        file_bytes=response.content,
        object_name=orig_key,
    )
    if not uploaded_url:
        raise Exception("Failed to upload original image to S3.")
    public_input_url = uploaded_url
    logger.info("Re-hosted Twilio image", extra={"url": public_input_url})

    return public_input_url


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
        start_time = time.perf_counter()
        fal_client = FalClient()

        # Get the current timestamp
        ts = int(time.time())

        # 0. If it's a Twilio URL, fetch & re-host first
        public_input_url = await _ensure_public_url(original_url, message_sid, ts)

        # 1. Stylize the image
        stylized_url = await fal_client.stylize_image(public_input_url)
        logger.info("Stylized image URL", extra={"url": stylized_url})

        # 2. Get image bytes from stylized URL
        image_bytes = await download_image_from_url(stylized_url)
        if not image_bytes:
            raise ValueError("No bytes downloaded from stylized URL.")
        logger.info("Image downloaded from stylized URL")

        # 3. Create a unique object name for the image
        styled_ext = os.path.splitext(urlparse(stylized_url).path)[1] or ".jpg"
        # Normalize styled extension
        styled_ext = styled_ext.lower()
        object_name = f"processed/{message_sid}_{ts}{styled_ext}"

        # 4. Upload (run blocking boto3 call in a thread)
        s3_url: str | None = await asyncio.to_thread(
            s3_service.upload_file,
            file_bytes=image_bytes,
            object_name=object_name,
        )

        # If the image is not uploaded, raise an error
        if s3_url is None:
            raise Exception("Failed to upload image to S3.")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
        logger.info(
            "Uploaded to S3",
            extra={"sid": message_sid, "url": s3_url, "elapsed_ms": elapsed_ms},
        )
        return s3_url

    except Exception:
        logger.exception("Error processing image", extra={"sid": message_sid})
        raise
