from __future__ import annotations

import dataclasses
import uuid
from typing import Any


@dataclasses.dataclass
class TraceEvent:
    """One LLM call's telemetry — mirrors the backend's `TraceIn` schema
    (backend/app/schemas/trace.py) so `to_dict()` can be posted as-is.

    `client_trace_id` is generated once, here, at event-creation time — not
    per HTTP attempt — so that if BackgroundTransport retries a send (network
    error, 5xx), the retry carries the *same* id and the backend's dedup logic
    treats it as a no-op instead of a duplicate trace.
    """

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
    client_trace_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)
