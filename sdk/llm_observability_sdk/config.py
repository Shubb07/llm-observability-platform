from __future__ import annotations

import os

from llm_observability_sdk.transport import BackgroundTransport

_transport: BackgroundTransport | None = None


def init(
    api_key: str | None = None,
    base_url: str | None = None,
    transport: BackgroundTransport | None = None,
) -> None:
    """Configure the SDK. Call once at application startup, before making any
    instrumented calls.

    api_key/base_url fall back to the LLMOBS_API_KEY / LLMOBS_BASE_URL env vars.
    Pass `transport` to supply your own (e.g. in tests, or to customize batching).
    """
    global _transport

    if transport is not None:
        _transport = transport
        return

    resolved_key = api_key or os.environ.get("LLMOBS_API_KEY")
    resolved_url = base_url or os.environ.get("LLMOBS_BASE_URL", "http://localhost:8000")

    if not resolved_key:
        raise ValueError(
            "An API key is required: pass api_key=... to init() or set LLMOBS_API_KEY"
        )

    _transport = BackgroundTransport(api_key=resolved_key, base_url=resolved_url)


def get_transport() -> BackgroundTransport:
    if _transport is None:
        raise RuntimeError(
            "llm_observability_sdk.init() must be called before making instrumented calls"
        )
    return _transport


def shutdown() -> None:
    """Flush and stop the background sender. Call on application shutdown to
    make sure the last batch of traces isn't lost."""
    global _transport
    if _transport is not None:
        _transport.shutdown()
        _transport = None
