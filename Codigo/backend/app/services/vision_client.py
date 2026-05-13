"""Wrapper for Google Cloud Vision DOCUMENT_TEXT_DETECTION."""
from google.cloud import vision


class VisionError(Exception):
    """Raised when the Vision API returns an error or fails."""


class VisionClient:
    """Thin wrapper that returns plain text from image/PDF bytes."""

    def __init__(self):
        self._client = vision.ImageAnnotatorClient()

    def extract_text(self, image_bytes: bytes) -> str:
        """Run DOCUMENT_TEXT_DETECTION on the bytes and return the full text.

        Raises VisionError if the API returns an error message.
        Returns "" if no text was detected.
        """
        image = vision.Image(content=image_bytes)
        response = self._client.document_text_detection(image=image)

        if response.error.message:
            raise VisionError(response.error.message)

        return response.full_text_annotation.text or ""
