"""Unit tests for pdf_text_extractor."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.pdf_text_extractor import PageText, extract_pages


def _mock_pdfplumber_pages(texts: list[str | None]):
    """Returns a context manager that yields a fake pdf with the given page texts."""
    pages = []
    for t in texts:
        page = MagicMock()
        page.extract_text.return_value = t
        pages.append(page)

    pdf = MagicMock()
    pdf.pages = pages
    cm = MagicMock()
    cm.__enter__.return_value = pdf
    cm.__exit__.return_value = False
    return cm


def test_extract_pages_returns_text_from_digital_pdf_without_calling_vision(fake_pdf_bytes):
    """PDF digital: pdfplumber retorna texto, Vision NUNCA é chamada."""
    fake_pdf = _mock_pdfplumber_pages(["page 1 text", "page 2 text"])
    fake_vision = MagicMock()

    with patch("app.services.pdf_text_extractor.pdfplumber.open", return_value=fake_pdf):
        result = extract_pages(fake_pdf_bytes, vision_client=fake_vision)

    assert result == [
        PageText(page_number=1, text="page 1 text"),
        PageText(page_number=2, text="page 2 text"),
    ]
    fake_vision.extract_text.assert_not_called()


def test_extract_pages_uses_vision_fallback_when_pdfplumber_returns_empty(fake_pdf_bytes):
    """PDF digitalizado: pdfplumber retorna None/'', cai no Vision."""
    fake_pdf = _mock_pdfplumber_pages([None])
    fake_vision = MagicMock()
    fake_vision.extract_text.return_value = "vision text"

    with patch("app.services.pdf_text_extractor.pdfplumber.open", return_value=fake_pdf), \
         patch("app.services.pdf_text_extractor._render_page_to_png", return_value=b"png_bytes"):
        result = extract_pages(fake_pdf_bytes, vision_client=fake_vision)

    assert result == [PageText(page_number=1, text="vision text")]
    fake_vision.extract_text.assert_called_once_with(b"png_bytes")


def test_extract_pages_only_falls_back_for_empty_pages(fake_pdf_bytes):
    """PDF misto: só páginas vazias caem no Vision."""
    fake_pdf = _mock_pdfplumber_pages(["digital", "", "another digital"])
    fake_vision = MagicMock()
    fake_vision.extract_text.return_value = "from vision"

    with patch("app.services.pdf_text_extractor.pdfplumber.open", return_value=fake_pdf), \
         patch("app.services.pdf_text_extractor._render_page_to_png", return_value=b"png_bytes"):
        result = extract_pages(fake_pdf_bytes, vision_client=fake_vision)

    assert result == [
        PageText(page_number=1, text="digital"),
        PageText(page_number=2, text="from vision"),
        PageText(page_number=3, text="another digital"),
    ]
    assert fake_vision.extract_text.call_count == 1


def test_extract_pages_raises_on_corrupted_pdf():
    """PDF corrompido: levanta exceção tratável."""
    with patch("app.services.pdf_text_extractor.pdfplumber.open", side_effect=Exception("corrupted")):
        with pytest.raises(Exception, match="corrupted"):
            extract_pages(b"not a pdf", vision_client=MagicMock())
