from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ProjectOut(BaseModel):
    id: str
    name: str
    api_key: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummary(BaseModel):
    id: str
    name: str
    status: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
