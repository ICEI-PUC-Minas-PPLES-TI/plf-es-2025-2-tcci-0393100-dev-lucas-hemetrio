import uuid
from datetime import datetime, timezone
from enum import Enum

from neomodel import DateTimeProperty, StringProperty, StructuredNode


def _utc_now():
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"


class Document(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    title = StringProperty(required=True)
    file_path = StringProperty(required=True)
    status = StringProperty(default=DocumentStatus.UPLOADING.value)
    created_at = DateTimeProperty(default=_utc_now)
