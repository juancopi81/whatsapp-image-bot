"""Configuration management for the WhatsApp Image Stylization Bot.

Loads environment variables and provides application settings.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application settings loaded from environment variables."""

    # TWILIO
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    # FAL
    FAL_KEY: Optional[str] = os.getenv("FAL_KEY")

    # AWS - S3
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: Optional[str] = os.getenv("AWS_REGION")
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")
