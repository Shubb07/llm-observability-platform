# SDK

Python package that wraps LLM provider calls and captures telemetry: prompt, completion,
model name, provider, token counts, latency, estimated cost, and error details.

## Install (local dev)

```bash
cd sdk
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # .venv/bin/pip on macOS/Linux
```

## Usage

```python
import openai
import llm_observability_sdk as obs
from llm_observability_sdk.integrations.openai import instrument_openai

obs.init(api_key="<project-api-key>", base_url="http://localhost:8000")

client = instrument_openai(openai.OpenAI())
client.chat.completions.create(model="gpt-4o", messages=[...])  # traced automatically

obs.shutdown()  # flush any buffered traces before the process exits
```

`instrument_anthropic` works the same way for `anthropic.Anthropic()`. For anything not
covered by a built-in integration, use the manual context manager:

```python
with obs.trace(model="my-model", provider="custom", prompt=prompt) as t:
    result = call_my_model(prompt)
    t.set_completion(result.text, result.prompt_tokens, result.completion_tokens)
```

The API key comes from a project created via the backend (`POST /api/v1/projects`); see
[`../backend/README.md`](../backend/README.md).

## Testing

```bash
.venv/Scripts/python -m pytest -q
```

## Layout

| File | Responsibility |
|---|---|
| `transport.py` | Background thread: buffers, batches, flushes with retry/backoff |
| `config.py` | `init()`/`shutdown()`/`get_transport()` — public wiring |
| `models.py` | `TraceEvent`, mirrors the backend's `TraceIn` schema |
| `pricing.py` | Per-model cost estimation |
| `manual.py` | `trace()` context manager for providers without a built-in integration |
| `integrations/openai.py` | `instrument_openai()` |
| `integrations/anthropic.py` | `instrument_anthropic()` |

Design constraints this SDK follows (PRD US-001, HLD reliability principles):

- Wrapping an existing call requires fewer than 5 lines of code change
- Telemetry capture never blocks the caller's thread — enqueue is synchronous, sending isn't
- Traces are batched and flushed asynchronously
- Buffered locally and retried with backoff if the backend is unreachable; a trace is never
  silently dropped on the client side
