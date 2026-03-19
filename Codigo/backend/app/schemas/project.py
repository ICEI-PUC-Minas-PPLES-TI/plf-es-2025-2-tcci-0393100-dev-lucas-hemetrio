from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str


class ProjectRename(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    name: str
    created_at: datetime