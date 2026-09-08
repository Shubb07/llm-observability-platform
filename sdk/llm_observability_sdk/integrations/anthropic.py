from __future__ import annotations

import time
from typing import Any

from llm_observability_sdk.config import get_transport
from llm_observability_sdk.integrations._utils import render_messages
from llm_observability_sdk.models import TraceEvent
from llm_observability_sdk.pricing import estimate_cost


def instrument_anthropic(client: Any) -> Any:
    """Wrap an Anthropic client instance so every `messages.create` call is traced.

    Usage:
        import anthropic
        from llm_observability_sdk.integrations.anthropic import instrument_anthropic

        client = instrument_anthropic(anthropic.Anthropic())
        client.messages.create(model="claude-sonnet-5", max_tokens=1024, messages=[...])  # traced
    """
    original_create = client.messages.create

    def traced_create(*args: Any, **kwargs: Any) -> Any:
        transport = get_transport()
        model = kwargs.get("model", "unknown")
        prompt = render_messages(kwargs.get("messages", []))
        start = time.perf_counter()

        try:
            response = original_create(*args, **kwargs)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            transport.enqueue(
                TraceEvent(
                    model=model,
                    provider="anthropic",
                    prompt=prompt,
                    latency_ms=latency_ms,
                    status="error",
                    error_message=str(exc),
                )
            )
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        completion = _render_content(response.content)
        prompt_tokens = getattr(response.usage, "input_tokens", 0) or 0
        completion_tokens = getattr(response.usage, "output_tokens", 0) or 0
        resolved_model = response.model or model

        transport.enqueue(
            TraceEvent(
                model=resolved_model,
                provider="anthropic",
                prompt=prompt,
                completion=completion,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=estimate_cost(resolved_model, prompt_tokens, completion_tokens),
                latency_ms=latency_ms,
                status="success",
            )
        )
        return response

    client.messages.create = traced_create
    return client


def _render_content(content: Any) -> str:
    parts = []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)
