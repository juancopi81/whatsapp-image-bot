"""Configuration management for the WhatsApp Image Stylization Bot.

Loads environment variables and provides application settings.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _read_secret(secret_name: str, env_var: str) -> Optional[str]:
    """Read secret from Docker secrets file or fall back to environment variable.

    Args:
    ----
        secret_name: Name of the Docker secret file
        env_var: Environment variable name to fall back to

    Returns:
    -------
        The secret value or None if not found

    """
    secret_path = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_path):
        with open(secret_path, 'r') as f:
            return f.read().strip()
    return os.getenv(env_var)


class Config:
    """Application settings loaded from environment variables or Docker secrets."""

    # TWILIO
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = _read_secret(
        "twilio_auth_token", "TWILIO_AUTH_TOKEN"
    )
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    # FAL
    FAL_KEY: Optional[str] = _read_secret("fal_key", "FAL_KEY")

    # AWS - S3
    AWS_ACCESS_KEY_ID: Optional[str] = _read_secret(
        "aws_access_key_id", "AWS_ACCESS_KEY_ID"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = _read_secret(
        "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY"
    )
    AWS_REGION: Optional[str] = os.getenv("AWS_REGION")
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")
