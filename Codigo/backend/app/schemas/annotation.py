from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    title: str
    type: str
    content: str
    position: str
    canvas_path: str
    document_uid: str | None
    status: str
    created_at: datetime
