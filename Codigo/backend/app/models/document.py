import uuid
from datetime import datetime, timezone
from enum import Enum

from neomodel import DateTimeProperty, RelationshipTo, StringProperty, StructuredNode


def _utc_now():
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class Document(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    title = StringProperty(required=True)
    file_path = StringProperty(required=True)
    status = StringProperty(default=DocumentStatus.PROCESSING.value)
    created_at = DateTimeProperty(default=_utc_now)
    annotations = RelationshipTo('app.models.annotation.Annotation', 'CONTAINS')
    pages = RelationshipTo('app.models.document_page.DocumentPage', 'HAS_PAGE')
