"""API routes for the WhatsApp Image Stylization Bot.

This module defines the main API router and includes the webhook endpoints.
"""

from fastapi import APIRouter

from whatsapp_image_bot.api import webhooks

# Main router for the API
api_router = APIRouter()

# Include the webhook router under the /webhooks path
# All routes defined in webhooks.py will now be prefixed with /webhooks
# For example, the "/" route in webhooks.py becomes "/webhooks/"
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
