"""Client for sending WhatsApp messages using the Twilio API.

This module provides the `WhatsAppClient` class, which acts as a high-level
wrapper for the Twilio REST API. It simplifies the process of sending
messages by handling authentication and the specifics of the API calls.

The client is designed to be a reusable service that can be integrated into
other parts of the application, such as the webhook handler, to send replies
back to users.
"""

from typing import Optional

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from twilio.rest.api.v2010.account.message import MessageInstance

from whatsapp_image_bot.config import Config
from whatsapp_image_bot.utils import get_logger

# --- Logger ---
logger = get_logger(__name__)


# --- WhatsApp Client ---
class WhatsAppClient:
    """Client for sending WhatsApp messages using the Twilio API."""

    def __init__(self) -> None:
        """Initialize the WhatsApp client."""
        self.config = Config()
        self.sender_phone_number = self.config.TWILIO_PHONE_NUMBER
        self.client = Client(
            self.config.TWILIO_ACCOUNT_SID, self.config.TWILIO_AUTH_TOKEN
        )

    def send_reply(
        self,
        to: str,
        body: str,
        media_url: Optional[str] = None,
    ) -> MessageInstance:
        """Sends a reply message via Twilio to a WhatsApp user.

        Args:
        ----
            to: The recipient's WhatsApp number in E.164 format.
            body: The text content of the message.
            media_url: An optional URL for an image to attach.

        Returns:
        -------
            The Twilio `MessageInstance` object if the message is sent
            successfully.

        Raises:
        ------
            TwilioRestException: If the API call to Twilio fails.

        """
        try:
            message = self.client.messages.create(
                to=to,
                from_=self.sender_phone_number,
                body=body,
                media_url=media_url,
            )
            logger.info(f"Reply sent to {to}. Message SID: {message.sid}")
            return message

        except TwilioRestException as e:
            logger.error(f"Error sending reply to {to}: {e}")
            raise e
