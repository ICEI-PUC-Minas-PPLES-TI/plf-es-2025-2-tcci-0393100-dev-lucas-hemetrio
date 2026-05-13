"""Unit tests for ocr_pipeline orchestration."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.ocr_pipeline import process_annotation, process_document
from app.services.pdf_text_extractor import PageText


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.read_file.return_value = b"%PDF-fake"
    return storage


@pytest.fixture
def mock_document():
    """Document mock that records save() calls."""
    doc = MagicMock()
    doc.uid = "doc-123"
    doc.file_path = "projects/p1/doc-123.pdf"
    doc.status = "PROCESSING"
    return doc


def test_process_document_indexes_pages_on_success(mock_storage, mock_document):
    pages_extracted = [
        PageText(page_number=1, text="page one"),
        PageText(page_number=2, text="page two"),
    ]

    with patch("app.services.ocr_pipeline._load_document", return_value=mock_document), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient"), \
         patch("app.services.ocr_pipeline.extract_pages", return_value=pages_extracted) as mock_extract, \
         patch("app.services.ocr_pipeline._save_pages") as mock_save_pages, \
         patch("app.services.ocr_pipeline._clear_existing_pages"):
        process_document("doc-123")

    mock_extract.assert_called_once()
    mock_save_pages.assert_called_once_with(mock_document, pages_extracted)
    assert mock_document.status == "INDEXED"
    mock_document.save.assert_called()


def test_process_document_marks_failed_when_extractor_raises(mock_storage, mock_document):
    with patch("app.services.ocr_pipeline._load_document", return_value=mock_document), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient"), \
         patch("app.services.ocr_pipeline.extract_pages", side_effect=Exception("boom")), \
         patch("app.services.ocr_pipeline._clear_existing_pages"):
        process_document("doc-123")

    assert mock_document.status == "FAILED"
    mock_document.save.assert_called()


def test_process_document_marks_failed_when_all_pages_empty(mock_storage, mock_document):
    pages_extracted = [
        PageText(page_number=1, text=""),
        PageText(page_number=2, text=""),
    ]

    with patch("app.services.ocr_pipeline._load_document", return_value=mock_document), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient"), \
         patch("app.services.ocr_pipeline.extract_pages", return_value=pages_extracted), \
         patch("app.services.ocr_pipeline._save_pages"), \
         patch("app.services.ocr_pipeline._clear_existing_pages"):
        process_document("doc-123")

    assert mock_document.status == "FAILED"


def test_process_document_indexes_when_at_least_one_page_has_text(mock_storage, mock_document):
    pages_extracted = [
        PageText(page_number=1, text=""),
        PageText(page_number=2, text="some text"),
    ]

    with patch("app.services.ocr_pipeline._load_document", return_value=mock_document), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient"), \
         patch("app.services.ocr_pipeline.extract_pages", return_value=pages_extracted), \
         patch("app.services.ocr_pipeline._save_pages"), \
         patch("app.services.ocr_pipeline._clear_existing_pages"):
        process_document("doc-123")

    assert mock_document.status == "INDEXED"


@pytest.fixture
def mock_annotation():
    ann = MagicMock()
    ann.uid = "ann-123"
    ann.canvas_image_path = "projects/p1/annotations/ann-123.png"
    ann.status = "PROCESSING"
    ann.extracted_text = ""
    return ann


def test_process_annotation_indexes_with_text_when_vision_succeeds(mock_annotation, mock_storage):
    mock_storage.read_file.return_value = b"png_bytes"
    fake_vision = MagicMock()
    fake_vision.extract_text.return_value = "handwritten text"

    with patch("app.services.ocr_pipeline._load_annotation", return_value=mock_annotation), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient", return_value=fake_vision):
        process_annotation("ann-123")

    assert mock_annotation.extracted_text == "handwritten text"
    assert mock_annotation.status == "INDEXED"
    mock_annotation.save.assert_called()


def test_process_annotation_indexes_with_empty_text_when_canvas_is_blank(mock_annotation, mock_storage):
    """Canvas em branco: Vision retorna '', mas é INDEXED (não é falha)."""
    mock_storage.read_file.return_value = b"png_bytes"
    fake_vision = MagicMock()
    fake_vision.extract_text.return_value = ""

    with patch("app.services.ocr_pipeline._load_annotation", return_value=mock_annotation), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient", return_value=fake_vision):
        process_annotation("ann-123")

    assert mock_annotation.extracted_text == ""
    assert mock_annotation.status == "INDEXED"


def test_process_annotation_marks_failed_when_vision_raises(mock_annotation, mock_storage):
    mock_storage.read_file.return_value = b"png_bytes"
    fake_vision = MagicMock()
    fake_vision.extract_text.side_effect = Exception("vision failure")

    with patch("app.services.ocr_pipeline._load_annotation", return_value=mock_annotation), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient", return_value=fake_vision):
        process_annotation("ann-123")

    assert mock_annotation.status == "FAILED"


def test_process_annotation_marks_failed_when_image_path_missing(mock_annotation, mock_storage):
    mock_annotation.canvas_image_path = ""
    fake_vision = MagicMock()

    with patch("app.services.ocr_pipeline._load_annotation", return_value=mock_annotation), \
         patch("app.services.ocr_pipeline.get_storage", return_value=mock_storage), \
         patch("app.services.ocr_pipeline.VisionClient", return_value=fake_vision):
        process_annotation("ann-123")

    assert mock_annotation.status == "FAILED"
    fake_vision.extract_text.assert_not_called()
