from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    page_number: int
    text: str
    created_at: datetime
