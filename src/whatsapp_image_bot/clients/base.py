"""Base class for all AI clients.

This class is used to process an image using an AI client.

The process_image method is used to remove a background or object from an image using an AI client.

The image_url is the URL of the image to process.

The prompt is the prompt to use to process the image.

"""

from abc import ABC, abstractmethod


class BaseAIClient(ABC):
    """Base class for all AI clients.

    This class is used to process an image using an AI client.
    """

    @abstractmethod
    def process_image(self, image_url: str, prompt: str) -> str:
        """Remove a background or object from an image using an AI client.

        Args:
        ----
            image_url: The URL of the image to process.
            prompt: The prompt to use to process the image.

        Returns:
        -------
            The URL of the processed image.

        """
        pass
