import uuid
from datetime import datetime, timezone

from neomodel import (
    BooleanProperty,
    DateTimeProperty,
    EmailProperty,
    StringProperty,
    StructuredNode,
)


def _utc_now():
    return datetime.now(timezone.utc)


class User(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    name = StringProperty(required=True)
    email = EmailProperty(unique_index=True, required=True)
    hashed_password = StringProperty(required=True)
    is_active = BooleanProperty(default=True)
    created_at = DateTimeProperty(default=_utc_now)