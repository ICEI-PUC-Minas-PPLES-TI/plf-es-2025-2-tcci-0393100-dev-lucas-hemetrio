import uuid
from datetime import datetime, timezone

from neomodel import (
    DateTimeProperty,
    IntegerProperty,
    RelationshipTo,
    StringProperty,
    StructuredNode,
)


def _utc_now():
    return datetime.now(timezone.utc)


class Mention(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    sentence_idx = IntegerProperty(required=True)
    sentence_text = StringProperty(required=True)
    surface_text = StringProperty(required=True)
    created_at = DateTimeProperty(default=_utc_now)

    entity = RelationshipTo('app.models.knowledge_node.KnowledgeNode', 'OF_ENTITY')
    from_page = RelationshipTo('app.models.document_page.DocumentPage', 'FROM_PAGE')
    from_annotation = RelationshipTo('app.models.annotation.Annotation', 'FROM_ANNOTATION')
