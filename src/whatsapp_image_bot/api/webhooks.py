"""Webhook handlers for the WhatsApp Image Stylization Bot.

This module contains the core logic for receiving and processing
incoming webhooks requests from Twilio.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Form

router = APIRouter()


# --- Pydantic Models for Webhook Requests ---
# Define a dependency class for the Twilio webhook data.
# FastAPI will automatically parse the incoming form data from Twilio
# and populate the fields of this class.
class TwilioWebhookRequest:
    """Data model for Twilio webhook requests."""

    def __init__(
        self,
        From: str = Form(...),
        To: str = Form(...),
        Body: Optional[str] = Form(None),
        NumMedia: int = Form(0),
        MediaUrl0: Optional[str] = Form(None),
        MessageSid: str = Form(...),
    ):
        """Initialize the Twilio webhook request with the form data from Twilio."""
        self.sender_number = From
        self.receiver_number = To
        self.body = Body
        self.num_media = NumMedia
        self.media_url = MediaUrl0
        self.message_sid = MessageSid


@router.post("/")
async def handle_incoming_message(
    webhook_request: TwilioWebhookRequest = Depends(),  # noqa: B008
):
    """Handle incoming messages from Twilio."""
    print("--- Incoming Webhook Data ---")
    print(f"SID: {webhook_request.message_sid}")
    print(f"From: {webhook_request.sender_number}")
    print(f"To: {webhook_request.receiver_number}")
    print(f"Body: {webhook_request.body}")
    print(f"NumMedia: {webhook_request.num_media}")
    if webhook_request.media_url:
        print(f"MediaUrl0: {webhook_request.media_url}")
    else:
        print("No media URL found")
    print("--- End of Incoming Webhook ---")
    return ""
