from datetime import datetime

from pydantic import BaseModel


class KnowledgeNodeOut(BaseModel):
    uid: str
    label: str
    text: str
    mention_count: int


class KnowledgeEdgeOut(BaseModel):
    source: str
    target: str
    weight: int


class KnowledgeGraphResponse(BaseModel):
    status: str
    updated_at: datetime | None
    nodes: list[KnowledgeNodeOut]
    edges: list[KnowledgeEdgeOut]
