"""Webhook handlers for the WhatsApp Image Stylization Bot.

This module receives Twilio webhooks, verifies authenticity, orchestrates image
stylization, and replies to the user. It keeps the FastAPI event-loop responsive
by running blocking Twilio calls in executor threads.
"""

import asyncio
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlparse

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, Field, ValidationError
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from whatsapp_image_bot.config import Config
from whatsapp_image_bot.services.image_processor import (
    MediaDownloadError,
    MediaValidationError,
    UploadError,
    process_image,
)
from whatsapp_image_bot.services.whatsapp_client import WhatsAppClient
from whatsapp_image_bot.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Reusable client (lightweight wrapper around Twilio REST).
_whatsapp_client = WhatsAppClient()


# ---------------------------------------------------------------------------
# Incoming webhook data model
# ---------------------------------------------------------------------------
class TwilioWebhookRequest(BaseModel):
    """Parsed payload for a Twilio WhatsApp webhook."""

    sender_number: str = Field(..., alias="From")
    message_sid: str = Field(..., alias="MessageSid")
    num_media: int = Field(..., alias="NumMedia")
    media_url: Optional[str] = Field(None, alias="MediaUrl0")

    def to_signature_dict(self) -> Dict[str, Any]:
        """Twilio signature validation needs the *original* form parameter names.

        Return only the fields we model; unmodeled fields are still validated
        via raw parse (see _parse_form_and_verify_signature).
        """
        return {
            "From": self.sender_number,
            "MessageSid": self.message_sid,
            "NumMedia": str(self.num_media),
            **({"MediaUrl0": self.media_url} if self.media_url else {}),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ALLOWED_MEDIA_SCHEMES = {"http", "https"}
ALLOWED_MEDIA_HOST_SUFFIXES = {
    "twilio.com",
    "api.twilio.com",
    "amazonaws.com",
    # Add other trusted domains
}


def _is_allowed_media_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_MEDIA_SCHEMES:
            return False
        host = (parsed.hostname or "").lower()
        return any(host.endswith(suf) for suf in ALLOWED_MEDIA_HOST_SUFFIXES)
    except Exception:
        return False


async def _safe_send_reply(*, to: str, body: str, media_url: str | None = None) -> None:
    """Run the blocking Twilio client send off-thread with logging guard."""
    try:
        await asyncio.to_thread(
            _whatsapp_client.send_reply,
            to=to,
            body=body,
            media_url=media_url,
        )
    except Exception:
        # Do not let a reply failure break the webhook 200 response to Twilio
        logger.exception("Failed to send WhatsApp reply", extra={"to": to})


def _twiml_empty() -> Response:
    """Return an empty TwiML ACK."""
    return Response(str(MessagingResponse()), media_type="application/xml")


async def _parse_form_and_verify_signature(request: Request) -> Dict[str, str]:
    """Read raw body, parse form fields before trust, and verify Twilio signature.

    Returns a dict of all form params (string -> string).

    IMPORTANT: Twilio signature uses the full URL including scheme + host + path + query.
    """
    cfg = Config()
    if not cfg.TWILIO_AUTH_TOKEN:
        logger.warning(
            "Twilio auth token missing; skipping signature verification (UNSAFE)."
        )
        body_bytes = await request.body()
        return dict(parse_qsl(body_bytes.decode("utf-8"), keep_blank_values=True))

    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    form_pairs = parse_qsl(body_str, keep_blank_values=True)
    params = dict(form_pairs)

    received_sig = request.headers.get("X-Twilio-Signature", "")
    validator = RequestValidator(cfg.TWILIO_AUTH_TOKEN)
    full_url = str(request.url)  # Twilio docs: use full URL

    if not validator.validate(full_url, params, received_sig):
        logger.warning("Twilio signature validation failed", extra={"url": full_url})
        # Intentionally return 403 without revealing details
        raise SignatureError("Invalid Twilio signature")

    return params


# Custom lightweight exception for clarity
class SignatureError(Exception):
    """Custom exception for signature validation errors."""

    pass


# ---------------------------------------------------------------------------
# Main webhook handler
# ---------------------------------------------------------------------------
@router.post("/")
async def handle_incoming_message(request: Request) -> Response:
    """Process an incoming WhatsApp message and reply accordingly.

    Steps:
        1. Verify Twilio signature
        2. Validate & parse payload
        3. Handle no-media vs. media flow
        4. Dispatch processing
    """
    try:
        raw_params = await _parse_form_and_verify_signature(request)
        logger.debug("Successfully parsed and verified Twilio signature")
    except SignatureError:
        # Deliberately minimal info; respond 403 so Twilio can notice & you can debug
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    except Exception:
        logger.exception("Unexpected error during signature verification")
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    # Parse into model (will raise ValidationError if mismatched)
    try:
        typed_params: Dict[str, Any] = dict(raw_params)  # widen value type

        # Explicit conversions (guard for presence)
        if "NumMedia" in typed_params:
            try:
                typed_params["NumMedia"] = int(typed_params["NumMedia"])
            except ValueError:
                typed_params["NumMedia"] = 0  # or raise / log

        webhook_request = TwilioWebhookRequest(**typed_params)
    except ValidationError as ve:
        logger.warning("Invalid Twilio webhook payload", extra={"errors": ve.errors()})
        return _twiml_empty()

    # ------------------------------------------------------------------
    # No image attached
    # ------------------------------------------------------------------
    if webhook_request.num_media == 0 or not webhook_request.media_url:
        logger.info(
            "Message without image attachment",
            extra={
                "sid": webhook_request.message_sid,
                "from": webhook_request.sender_number,
            },
        )
        await _safe_send_reply(
            to=webhook_request.sender_number,
            body="Please send an image to get it stylized! 🖼️",
        )
        return _twiml_empty()

    # ------------------------------------------------------------------
    # Validate media URL origin (basic allow-list)
    # ------------------------------------------------------------------
    if not _is_allowed_media_url(webhook_request.media_url):
        logger.warning(
            "Rejected media URL (not in allow-list)",
            extra={
                "sid": webhook_request.message_sid,
                "url": webhook_request.media_url,
            },
        )
        await _safe_send_reply(
            to=webhook_request.sender_number,
            body="That media host is not supported. Please resend an image from WhatsApp directly.",
        )
        return _twiml_empty()

    # ------------------------------------------------------------------
    # Acknowledge receipt
    # ------------------------------------------------------------------
    logger.info(
        "Image received - starting stylization",
        extra={
            "sid": webhook_request.message_sid,
            "from": webhook_request.sender_number,
        },
    )
    await _safe_send_reply(
        to=webhook_request.sender_number,
        body="Got it! Stylizing your image now… This might take a moment. ✨",
    )

    # ------------------------------------------------------------------
    # Process image
    # ------------------------------------------------------------------
    try:
        final_url = await process_image(
            original_url=webhook_request.media_url,
            message_sid=webhook_request.message_sid,
        )
    except MediaValidationError as ve:
        # Anticipated validation issues (e.g. unsupported MIME later)
        logger.warning(
            "Image validation error",
            extra={"sid": webhook_request.message_sid, "error": str(ve)},
        )
        error_str = str(ve).lower()
        if "size limit" in error_str:
            reply_body = "The image is too large. Please send one under 5MB. 📏"
        elif "media type" in error_str:
            reply_body = (
                "That image format isn't supported. Please send a JPG, PNG, or WEBP. 🖼️"
            )
        else:
            reply_body = (
                "That image could not be processed (validation error). Try another one."
            )
        await _safe_send_reply(to=webhook_request.sender_number, body=reply_body)
    except (MediaDownloadError, UploadError) as e:
        logger.warning(
            "Image processing error",
            extra={"sid": webhook_request.message_sid, "error": str(e)},
        )
        await _safe_send_reply(
            to=webhook_request.sender_number,
            body="There was a problem downloading or saving your image. Please try again.",
        )
    except Exception:
        logger.exception(
            "Unhandled error processing image",
            extra={"sid": webhook_request.message_sid},
        )
        await _safe_send_reply(
            to=webhook_request.sender_number,
            body="Sorry, something went wrong while stylizing your image. Please try again later. 😟",
        )
    else:
        await _safe_send_reply(
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

    return _twiml_empty()
