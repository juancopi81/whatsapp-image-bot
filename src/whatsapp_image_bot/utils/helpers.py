"""Helper functions for the WhatsApp Image Stylization Bot."""

import httpx


async def download_image_from_url(url: str) -> bytes:
    """Download an image from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content
