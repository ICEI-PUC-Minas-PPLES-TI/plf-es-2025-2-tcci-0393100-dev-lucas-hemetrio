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


class MentionOut(BaseModel):
    uid: str
    sentence_text: str
    source_type: str  # "document" | "annotation"
    source_uid: str
    source_title: str
    page_number: int | None = None


class MentionsListResponse(BaseModel):
    node: KnowledgeNodeOut
    mentions: list[MentionOut]


class CoOccurrenceOut(BaseModel):
    sentence_text: str
    source_type: str
    source_uid: str
    source_title: str
    page_number: int | None = None


class CoOccurrencesResponse(BaseModel):
    node_a: KnowledgeNodeOut
    node_b: KnowledgeNodeOut
    weight: int
    co_occurrences: list[CoOccurrenceOut]
