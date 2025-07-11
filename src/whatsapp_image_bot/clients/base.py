"""Base class for all AI clients.

This class is used to stylize an image using an AI client.
"""

from abc import ABC, abstractmethod


class BaseAIClient(ABC):
    """Base class for all AI clients.

    This class is used to stylize an image using an AI client.
    """

    @abstractmethod
    def stylize_image(self, image_url: str) -> str:
        """Stylize an image using an AI client.

        Args:
        ----
            image_url: The URL of the image to stylize.

        Returns:
        -------
            The URL of the stylized image.

        """
        pass
