import uuid
from datetime import datetime, timezone
from enum import Enum

from neomodel import DateTimeProperty, StringProperty, StructuredNode


def _utc_now():
    return datetime.now(timezone.utc)


class AnnotationType(str, Enum):
    HANDWRITING = "HANDWRITING"
    TEXT = "TEXT"


class Annotation(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    title = StringProperty(required=True)
    type = StringProperty(default=AnnotationType.HANDWRITING.value)
    content = StringProperty(default="")
    position = StringProperty(default="")
    canvas_path = StringProperty(required=True)
    document_uid = StringProperty(default=None)
    status = StringProperty(default="UPLOADING")
    created_at = DateTimeProperty(default=_utc_now)
