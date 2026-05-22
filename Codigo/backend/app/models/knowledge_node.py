import uuid
from datetime import datetime, timezone

from neomodel import (
    DateTimeProperty,
    IntegerProperty,
    Relationship,
    RelationshipFrom,
    StringProperty,
    StructuredNode,
    StructuredRel,
)


def _utc_now():
    return datetime.now(timezone.utc)


class CoOccursWithRel(StructuredRel):
    weight = IntegerProperty(default=1)


class KnowledgeNode(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    label = StringProperty(required=True)
    text_norm = StringProperty(required=True)
    text_display = StringProperty(required=True)
    mention_count = IntegerProperty(default=0)
    created_at = DateTimeProperty(default=_utc_now)

    co_occurs_with = Relationship(
        'app.models.knowledge_node.KnowledgeNode',
        'CO_OCCURS_WITH',
        model=CoOccursWithRel,
    )
    project = RelationshipFrom('app.models.project.Project', 'HAS_KNOWLEDGE_NODE')
