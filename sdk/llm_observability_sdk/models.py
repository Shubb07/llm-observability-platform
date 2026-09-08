from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class TraceEvent:
    """One LLM call's telemetry — mirrors the backend's `TraceIn` schema
    (backend/app/schemas/trace.py) so `to_dict()` can be posted as-is."""

    model: str
    provider: str
    prompt: str
    latency_ms: float
    completion: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    status: str = "success"
    error_message: str | None = None
    tags: dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)
