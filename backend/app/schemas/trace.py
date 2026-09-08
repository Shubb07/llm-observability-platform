from datetime import datetime

from pydantic import BaseModel, Field


class TraceIn(BaseModel):
    model: str
    provider: str
    prompt: str
    completion: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float
    cost: float = 0.0
    status: str = "success"
    error_message: str | None = None
    tags: dict = Field(default_factory=dict)


class TraceBatchIn(BaseModel):
    traces: list[TraceIn] = Field(min_length=1, max_length=500)


class TraceOut(BaseModel):
    id: str
    project_id: str
    model: str
    provider: str
    prompt: str
    completion: str | None
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cost: float
    status: str
    error_message: str | None
    tags: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class TraceListOut(BaseModel):
    items: list[TraceOut]
    total: int
    limit: int
    offset: int
