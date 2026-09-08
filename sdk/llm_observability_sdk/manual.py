from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Iterator

from llm_observability_sdk.config import get_transport
from llm_observability_sdk.models import TraceEvent


class TraceRecorder:
    """Filled in by the caller inside a `trace()` block."""

    def __init__(self) -> None:
        self.completion: str | None = None
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.cost: float = 0.0
        self.tags: dict[str, Any] = {}

    def set_completion(
        self,
        completion: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        self.completion = completion
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.cost = cost


@contextmanager
def trace(
    model: str,
    provider: str,
    prompt: str,
    tags: dict[str, Any] | None = None,
) -> Iterator[TraceRecorder]:
    """Manually record an LLM call not covered by a built-in integration
    (`instrument_openai`, `instrument_anthropic`).

    Usage:
        with trace(model="my-local-model", provider="custom", prompt=prompt) as t:
            result = call_my_model(prompt)
            t.set_completion(result.text, result.prompt_tokens, result.completion_tokens)

    An exception raised inside the block is recorded as a failed trace and
    re-raised — it is never swallowed.
    """
    recorder = TraceRecorder()
    if tags:
        recorder.tags = tags

    transport = get_transport()
    start = time.perf_counter()

    try:
        yield recorder
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        transport.enqueue(
            TraceEvent(
                model=model,
                provider=provider,
                prompt=prompt,
                latency_ms=latency_ms,
                status="error",
                error_message=str(exc),
                tags=recorder.tags,
            )
        )
        raise
    else:
        latency_ms = (time.perf_counter() - start) * 1000
        transport.enqueue(
            TraceEvent(
                model=model,
                provider=provider,
                prompt=prompt,
                completion=recorder.completion,
                prompt_tokens=recorder.prompt_tokens,
                completion_tokens=recorder.completion_tokens,
                cost=recorder.cost,
                latency_ms=latency_ms,
                status="success",
                tags=recorder.tags,
            )
        )
