from pydantic import BaseModel


class SearchProjectRef(BaseModel):
    uid: str
    name: str


class SearchDocumentRef(BaseModel):
    uid: str
    title: str


class SearchAnnotationRef(BaseModel):
    uid: str
    title: str


class SearchPageHit(BaseModel):
    page_number: int
    snippet: str
    score: float


class SearchTitleMatch(BaseModel):
    snippet: str


class SearchDocumentGroup(BaseModel):
    document: SearchDocumentRef
    title_match: SearchTitleMatch | None = None
    page_hits: list[SearchPageHit] = []


class SearchAnnotationHit(BaseModel):
    annotation: SearchAnnotationRef
    snippet: str
    score: float


class SearchProjectGroup(BaseModel):
    project: SearchProjectRef
    documents: list[SearchDocumentGroup] = []
    annotations: list[SearchAnnotationHit] = []


class SearchResponse(BaseModel):
    query: str
    total: int
    results_by_project: list[SearchProjectGroup]
