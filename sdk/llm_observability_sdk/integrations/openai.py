from __future__ import annotations

import time
from typing import Any

from llm_observability_sdk.config import get_transport
from llm_observability_sdk.integrations._utils import render_messages
from llm_observability_sdk.models import TraceEvent
from llm_observability_sdk.pricing import estimate_cost


def instrument_openai(client: Any) -> Any:
    """Wrap an OpenAI client instance so every chat completion is traced.

    Usage:
        import openai
        from llm_observability_sdk.integrations.openai import instrument_openai

        client = instrument_openai(openai.OpenAI())
        client.chat.completions.create(model="gpt-4o", messages=[...])  # traced

    Only `client.chat.completions.create` is wrapped (the PRD's target
    surface). The client's own type is untouched — this duck-types onto
    whatever is passed in, so no `openai` import is required by this module.
    """
    original_create = client.chat.completions.create

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
                    provider="openai",
                    prompt=prompt,
                    latency_ms=latency_ms,
                    status="error",
                    error_message=str(exc),
                )
            )
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        completion = response.choices[0].message.content if response.choices else None
        prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
        resolved_model = response.model or model

        transport.enqueue(
            TraceEvent(
                model=resolved_model,
                provider="openai",
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

    client.chat.completions.create = traced_create
    return client
