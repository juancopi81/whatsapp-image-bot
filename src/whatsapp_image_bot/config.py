"""Configuration management for the WhatsApp Image Stylization Bot.

Loads environment variables and provides application settings.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application settings loaded from environment variables."""

    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    FAL_API_KEY: Optional[str] = os.getenv("FAL_API_KEY")
