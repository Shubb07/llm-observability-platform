# SDK

Python package that wraps LLM provider calls and captures telemetry: prompt, completion,
model name, provider, token counts, latency, estimated cost, and error details.

Responsibilities (see HLD → Components → Python SDK, PRD → US-001):

- Installable via `pip` in one command
- Wrapping an existing LLM call requires fewer than 5 lines of code change
- Captures telemetry without blocking the main application thread
- Batches traces and flushes them asynchronously to the backend
- Buffers locally and retries with backoff if the backend is unreachable

Package skeleton lives in `llm_observability_sdk/`. Not implemented yet.
