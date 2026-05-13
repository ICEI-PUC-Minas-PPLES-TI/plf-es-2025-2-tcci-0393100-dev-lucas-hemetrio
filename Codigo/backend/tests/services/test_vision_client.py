"""Unit tests for vision_client wrapper."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.vision_client import VisionClient, VisionError


def _mock_response(text: str):
    response = MagicMock()
    response.error.message = ""
    response.full_text_annotation.text = text
    return response


def test_extract_text_returns_text_from_image_bytes(fake_png_bytes):
    fake_response = _mock_response("Hello world")
    with patch("app.services.vision_client.vision.ImageAnnotatorClient") as mock_cls:
        mock_cls.return_value.document_text_detection.return_value = fake_response

        client = VisionClient()
        result = client.extract_text(fake_png_bytes)

    assert result == "Hello world"


def test_extract_text_raises_vision_error_on_api_error(fake_png_bytes):
    response = MagicMock()
    response.error.message = "QUOTA_EXCEEDED"
    response.full_text_annotation.text = ""
    with patch("app.services.vision_client.vision.ImageAnnotatorClient") as mock_cls:
        mock_cls.return_value.document_text_detection.return_value = response

        client = VisionClient()
        with pytest.raises(VisionError, match="QUOTA_EXCEEDED"):
            client.extract_text(fake_png_bytes)


def test_extract_text_returns_empty_string_when_no_text_detected(fake_png_bytes):
    fake_response = _mock_response("")
    with patch("app.services.vision_client.vision.ImageAnnotatorClient") as mock_cls:
        mock_cls.return_value.document_text_detection.return_value = fake_response

        client = VisionClient()
        result = client.extract_text(fake_png_bytes)

    assert result == ""
