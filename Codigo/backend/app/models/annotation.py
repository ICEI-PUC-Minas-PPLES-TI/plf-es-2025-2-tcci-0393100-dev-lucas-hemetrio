import uuid
from datetime import datetime, timezone
from enum import Enum

from neomodel import DateTimeProperty, StringProperty, StructuredNode


def _utc_now():
    return datetime.now(timezone.utc)


class AnnotationStatus(str, Enum):
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class Annotation(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    title = StringProperty(required=True)
    content = StringProperty(default="")
    position = StringProperty(default="")
    canvas_path = StringProperty(required=True)
    canvas_image_path = StringProperty(default="")
    document_uid = StringProperty(default=None)
    status = StringProperty(default=AnnotationStatus.PROCESSING.value)
    extracted_text = StringProperty(default="")
    created_at = DateTimeProperty(default=_utc_now)
