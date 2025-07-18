"""Webhook handlers for the WhatsApp Image Stylization Bot.

This module receives Twilio webhooks, orchestrates image stylization, and
replies to the user. It keeps the FastAPI event-loop responsive by running
blocking Twilio calls in executor threads.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Form, Response
from pydantic import BaseModel, Field
from twilio.twiml.messaging_response import MessagingResponse

from whatsapp_image_bot.services.image_processor import process_image
from whatsapp_image_bot.services.whatsapp_client import WhatsAppClient
from whatsapp_image_bot.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Incoming webhook data model (parsed from Twilio form‑encoded payload)
# ---------------------------------------------------------------------------
class TwilioWebhookRequest(BaseModel):
    """Parsed payload for a Twilio WhatsApp webhook."""

    sender_number: str = Field(
        ...,
        description="Sender (WhatsApp) number in E.164 format",
        alias="From",
        title="Sender (WhatsApp) number in E.164 format",
    )
    message_sid: str = Field(
        ...,
        description="Unique ID for this inbound message",
        alias="MessageSid",
        title="Unique ID for this inbound message",
    )
    num_media: int = Field(
        ...,
        description="How many media items were attached",
        alias="NumMedia",
        title="How many media items were attached",
    )
    media_url: Optional[str] = Field(
        None,
        description="URL of the first media item",
        alias="MediaUrl0",
        title="URL of the first media item",
    )

    # FastAPI cannot yet infer "application/x-www-form-urlencoded" into a
    # Pydantic model directly.  The ``as_form`` helper bridges that gap so the
    # model can still be injected with ``Depends`` *and* retain runtime
    # validation + OpenAPI docs.
    @classmethod
    def as_form(  # noqa: N802 – keep Twilio’s original field names
        cls,
        From: str = Form(...),  # sender WhatsApp number
        MessageSid: str = Form(...),  # unique inbound message SID
        NumMedia: int = Form(0),  # number of media attachments
        MediaUrl0: Optional[str] = Form(None),  # first media URL (if any)
    ) -> "TwilioWebhookRequest":  # noqa: N803 – Twilio naming
        """Create a TwilioWebhookRequest from form data."""
        return cls(
            From=From,
            MessageSid=MessageSid,
            NumMedia=NumMedia,
            MediaUrl0=MediaUrl0,
        )


# ---------------------------------------------------------------------------
# Main webhook handler
# ---------------------------------------------------------------------------


@router.post("/")
async def handle_incoming_message(
    webhook_request: TwilioWebhookRequest = Depends(  # noqa: B008 – FastAPI pattern
        TwilioWebhookRequest.as_form,
    ),
) -> Response:
    """Process an incoming WhatsApp message and reply accordingly."""
    # Use a single client instance per request; run its sync methods off-thread
    whatsapp_client = WhatsAppClient()

    # ------------------------------------------------------------------
    # No image attached – ask the user for one
    # ------------------------------------------------------------------
    if webhook_request.num_media == 0 or not webhook_request.media_url:
        logger.warning(
            "Received message without image attachment.",
            extra={
                "sid": webhook_request.message_sid,
                "from": webhook_request.sender_number,
            },
        )
        await asyncio.to_thread(
            whatsapp_client.send_reply,
            to=webhook_request.sender_number,
            body="Please send an image to get it stylized! 🖼️",
        )
        return Response(str(MessagingResponse()), media_type="application/xml")

    # ------------------------------------------------------------------
    # Image received – acknowledge and start processing
    # ------------------------------------------------------------------
    logger.info(
        "Image received - starting stylization",
        extra={
            "sid": webhook_request.message_sid,
            "from": webhook_request.sender_number,
        },
    )
    await asyncio.to_thread(
        whatsapp_client.send_reply,
        to=webhook_request.sender_number,
        body="Got it! Stylizing your image now… This might take a moment. ✨",
    )

    # ------------------------------------------------------------------
    # Run the heavy lifting: stylize + upload
    # ------------------------------------------------------------------
    try:
        final_url = await process_image(
            original_url=webhook_request.media_url,  # type: ignore[arg-type]
            message_sid=webhook_request.message_sid,
        )

        # Send back the stylized image
        await asyncio.to_thread(
            whatsapp_client.send_reply,
            to=webhook_request.sender_number,
            body="Here's your stylized image! 🖼️",
            media_url=final_url,
        )
        logger.info(
            "Stylized image sent",
            extra={
                "sid": webhook_request.message_sid,
                "to": webhook_request.sender_number,
            },
        )
    except Exception as exc:
        logger.error(
            "Failed to process image",
            exc_info=True,
            extra={
                "sid": webhook_request.message_sid,
                "error": str(exc),
            },
        )
        await asyncio.to_thread(
            whatsapp_client.send_reply,
            to=webhook_request.sender_number,
            body="Sorry, something went wrong while stylizing your image. Please try again later. 😟",
        )

    # ------------------------------------------------------------------
    # Always return an empty TwiML response; Twilio only needs ACK.
    # ------------------------------------------------------------------
    return Response(str(MessagingResponse()), media_type="application/xml")
