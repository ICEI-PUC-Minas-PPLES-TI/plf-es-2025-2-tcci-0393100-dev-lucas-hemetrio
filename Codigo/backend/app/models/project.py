import uuid
from datetime import datetime, timezone

from neomodel import DateTimeProperty, RelationshipTo, StringProperty, StructuredNode


def _utc_now():
    return datetime.now(timezone.utc)


class Project(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    name = StringProperty(required=True)
    created_at = DateTimeProperty(default=_utc_now)
    documents = RelationshipTo('app.models.document.Document', 'CONTAINS')