from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    title: str
    file_path: str
    status: DocumentStatus
    created_at: datetime
