"""Orchestrates OCR/HCR pipeline for documents and annotations.

Sole module that talks to Neo4j for status transitions.
Always catches exceptions to avoid leaving items stuck in PROCESSING.
"""
import logging

from app.models.annotation import Annotation, AnnotationStatus
from app.models.document import Document, DocumentStatus
from app.models.document_page import DocumentPage
from app.services.pdf_text_extractor import extract_pages
from app.services.vision_client import VisionClient
from app.storage import get_storage

logger = logging.getLogger(__name__)


def _load_document(doc_uid: str) -> Document | None:
    return Document.nodes.get_or_none(uid=doc_uid)


def _load_annotation(ann_uid: str) -> Annotation | None:
    return Annotation.nodes.get_or_none(uid=ann_uid)


def _save_pages(document: Document, pages: list) -> None:
    """Persist DocumentPage nodes and connect them to the document."""
    for page in pages:
        node = DocumentPage(page_number=page.page_number, text=page.text).save()
        document.pages.connect(node)


def _clear_existing_pages(document: Document) -> None:
    for page in document.pages.all():
        document.pages.disconnect(page)
        page.delete()


def process_document(doc_uid: str) -> None:
    """Background task: extract text from PDF and persist DocumentPages.

    Status transitions: PROCESSING -> INDEXED | FAILED.
    Never raises - catches everything and marks FAILED on error.
    """
    document = _load_document(doc_uid)
    if document is None:
        logger.error("process_document: doc_uid=%s not found", doc_uid)
        return

    try:
        _clear_existing_pages(document)
        storage = get_storage()
        pdf_bytes = storage.read_file(document.file_path)
        vision_client = VisionClient()
        pages = extract_pages(pdf_bytes, vision_client=vision_client)

        _save_pages(document, pages)

        has_any_text = any(p.text.strip() for p in pages)
        document.status = (
            DocumentStatus.INDEXED.value if has_any_text else DocumentStatus.FAILED.value
        )
        document.save()
        logger.info(
            "process_document: doc_uid=%s status=%s pages=%d",
            doc_uid, document.status, len(pages),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("process_document: doc_uid=%s failed: %s", doc_uid, exc)
        document.status = DocumentStatus.FAILED.value
        document.save()


def process_annotation(ann_uid: str) -> None:
    """Background task: run HCR on the annotation's PNG and persist text.

    Status transitions: PROCESSING -> INDEXED | FAILED.
    Empty extracted text (blank canvas) is INDEXED, not FAILED.
    Never raises - catches everything and marks FAILED on error.
    """
    annotation = _load_annotation(ann_uid)
    if annotation is None:
        logger.error("process_annotation: ann_uid=%s not found", ann_uid)
        return

    try:
        if not annotation.canvas_image_path:
            raise ValueError("canvas_image_path is empty")

        storage = get_storage()
        png_bytes = storage.read_file(annotation.canvas_image_path)
        vision_client = VisionClient()
        text = vision_client.extract_text(png_bytes)

        annotation.extracted_text = text
        annotation.status = AnnotationStatus.INDEXED.value
        annotation.save()
        logger.info(
            "process_annotation: ann_uid=%s status=INDEXED text_len=%d",
            ann_uid, len(text),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("process_annotation: ann_uid=%s failed: %s", ann_uid, exc)
        annotation.status = AnnotationStatus.FAILED.value
        annotation.save()
