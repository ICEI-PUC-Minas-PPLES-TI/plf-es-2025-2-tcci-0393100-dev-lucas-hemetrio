"""Extract text from PDF, page by page, with Vision fallback for empty pages."""
import io
from dataclasses import dataclass

import pdfplumber

from app.services.vision_client import VisionClient


@dataclass(frozen=True)
class PageText:
    page_number: int  # 1-indexed
    text: str


def _render_page_to_png(page) -> bytes:
    """Render a pdfplumber page to PNG bytes."""
    image = page.to_image(resolution=200)
    buf = io.BytesIO()
    image.original.save(buf, format="PNG")
    return buf.getvalue()


def extract_pages(pdf_bytes: bytes, vision_client: VisionClient) -> list[PageText]:
    """Open the PDF and extract text from each page.

    For each page:
    - Tries pdfplumber.extract_text() first.
    - If empty/None, renders the page to PNG and calls vision_client.extract_text().

    Returns a list of PageText, ordered by page_number (1-indexed).
    Raises whatever pdfplumber raises if the PDF is invalid.
    """
    results: list[PageText] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                results.append(PageText(page_number=index, text=text))
                continue

            png_bytes = _render_page_to_png(page)
            vision_text = vision_client.extract_text(png_bytes)
            results.append(PageText(page_number=index, text=vision_text))

    return results
