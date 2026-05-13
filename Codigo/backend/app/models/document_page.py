import uuid
from datetime import datetime, timezone

from neomodel import DateTimeProperty, IntegerProperty, StringProperty, StructuredNode


def _utc_now():
    return datetime.now(timezone.utc)


class DocumentPage(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    page_number = IntegerProperty(required=True)
    text = StringProperty(default="")
    created_at = DateTimeProperty(default=_utc_now)
