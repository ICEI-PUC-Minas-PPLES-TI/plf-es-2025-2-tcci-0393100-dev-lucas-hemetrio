import uuid
from datetime import datetime, timezone

from neomodel import DateTimeProperty, RelationshipTo, StringProperty, StructuredNode


def _utc_now():
    return datetime.now(timezone.utc)


class ProjectKnowledgeStatus:
    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Project(StructuredNode):
    uid = StringProperty(unique_index=True, default=lambda: str(uuid.uuid4()))
    name = StringProperty(required=True)
    created_at = DateTimeProperty(default=_utc_now)
    knowledge_status = StringProperty(default=ProjectKnowledgeStatus.IDLE)
    knowledge_updated_at = DateTimeProperty(default=None)
    documents = RelationshipTo('app.models.document.Document', 'CONTAINS')
    annotations = RelationshipTo('app.models.annotation.Annotation', 'CONTAINS')
    knowledge_nodes = RelationshipTo(
        'app.models.knowledge_node.KnowledgeNode', 'HAS_KNOWLEDGE_NODE'
    )
