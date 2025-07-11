"""Client for interacting with the fal.ai image stylization API.

This client is used to stylize an image using the fal.ai API.
"""

import fal_client

from whatsapp_image_bot.utils.logger import get_logger

from .base import BaseAIClient

# The ID of the model we want to use from fal.ai
MODEL_ID = "fal-ai/flux-pro/kontext/max"
logger = get_logger(__name__)


class FalClient(BaseAIClient):
    """A client for interacting with the fal.ai image stylization API."""

    async def stylize_image(self, image_url: str) -> str:
        """Stylizes an image using the fal.ai API.

        This method sends a request to the specified model with a prompt
        and an image URL, waits for the result, and returns the URL
        of the stylized image.

        Args:
        ----
            image_url: The URL of the image to stylize.

        Returns:
        -------
            The URL of the stylized image.

        Raises:
        ------
            Exception: If the API call fails or returns no images.

        """
        logger.info("Sending request to fal.ai for image: %s", image_url)

        try:
            # Prepare the arguments for the API call
            arguments = {
                "prompt": "Change to Simpsons style while maintaining the original composition and object placement",
                "image_url": image_url,
            }

            # Use the async method to submit the job
            handler = await fal_client.submit_async(MODEL_ID, arguments=arguments)

            # Wait for the job to complete and get the result
            result = await handler.get()

            # Extract the URL of the first image from the response
            if result and "images" in result and len(result["images"]) > 0:
                stylized_url = result["images"][0]["url"]
                logger.info(
                    "Successfully received stylized image URL: %s", stylized_url
                )
                return stylized_url
            else:
                raise Exception("API call succeeded but returned no images.")

        except Exception:
            logger.error("Error calling fal.ai", exc_info=True)
            raise
