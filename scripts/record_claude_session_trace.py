"""Claude Code "Stop" hook: record this session's own prompt/response pair
as a trace in the LLM Observability Platform - the same backend everything
else in this project reports to, just observing Claude Code itself instead
of a wrapped OpenAI/Gemini/Anthropic client.

Why a Stop hook and not the SDK's instrument_anthropic(): there's no client
object here to wrap - Claude Code calls the Anthropic API internally, not
through user code this project controls. The hook reads the session's own
transcript (which Claude Code already writes to disk) after each response
completes, pulls the latest prompt/response pair out of it, and posts that
to the same /api/v1/traces endpoint the SDK uses.

Needs LLMOBS_API_KEY set in the environment (a project's API key, from its
dashboard page) - never hardcode a real key here. If it's unset, or
anything else goes wrong, this exits 0 and does nothing rather than
interrupting the Claude Code session - same "never break the thing being
observed" principle the SDK's transport.py follows.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))
from llm_observability_sdk.pricing import estimate_cost  # noqa: E402

BASE_URL = os.environ.get("LLMOBS_BASE_URL", "https://llm-observability-backend-48ov.onrender.com")
API_KEY = os.environ.get("LLMOBS_API_KEY")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _text_from_content(content) -> str | None:
    """A turn's `message.content` is either a plain string, or a list of
    content blocks (text/tool_use/tool_result/...). Only plain strings and
    `type: "text"` blocks represent something a human or Claude actually
    wrote in the conversation - tool_use/tool_result are mechanics, not
    prompt/response text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [block.get("text") for block in content if isinstance(block, dict) and block.get("type") == "text"]
        parts = [p for p in parts if p]
        return "\n".join(parts) if parts else None
    return None


def _is_real_user_prompt(text: str) -> bool:
    # Hook-injected / system-generated content (command output, reminders,
    # compaction summaries) always arrives wrapped in a tag like this -
    # skip it so we only record what the user actually typed.
    return not text.lstrip().startswith("<")


def find_last_exchange(transcript_path: str) -> tuple[dict, dict] | None:
    """Returns (user_turn, assistant_turn) for the most recent real
    prompt/response pair, or None if the transcript doesn't have one yet."""
    turns = []
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                turns.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    assistant_turn = None
    for turn in reversed(turns):
        if turn.get("type") == "assistant":
            text = _text_from_content(turn.get("message", {}).get("content"))
            if text:
                assistant_turn = turn
                break
    if assistant_turn is None:
        return None

    assistant_index = turns.index(assistant_turn)
    for turn in reversed(turns[:assistant_index]):
        if turn.get("type") == "user":
            text = _text_from_content(turn.get("message", {}).get("content"))
            if text and _is_real_user_prompt(text):
                return turn, assistant_turn
    return None


def main() -> None:
    if not API_KEY:
        return

    hook_input = json.load(sys.stdin)
    transcript_path = hook_input.get("transcript_path")
    if not transcript_path or not os.path.exists(transcript_path):
        return

    exchange = find_last_exchange(transcript_path)
    if exchange is None:
        return
    user_turn, assistant_turn = exchange

    prompt = _text_from_content(user_turn["message"]["content"])
    completion = _text_from_content(assistant_turn["message"]["content"])
    model = assistant_turn["message"].get("model", "unknown")
    usage = assistant_turn["message"].get("usage", {})
    prompt_tokens = usage.get("input_tokens", 0) or 0
    completion_tokens = usage.get("output_tokens", 0) or 0

    try:
        latency_ms = (
            _parse_timestamp(assistant_turn["timestamp"]) - _parse_timestamp(user_turn["timestamp"])
        ).total_seconds() * 1000
    except (KeyError, ValueError):
        latency_ms = 0.0

    payload = {
        "traces": [
            {
                "client_trace_id": assistant_turn["uuid"],
                "model": model,
                "provider": "anthropic",
                "prompt": prompt,
                "completion": completion,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": max(latency_ms, 0.0),
                "cost": estimate_cost(model, prompt_tokens, completion_tokens),
                "status": "success",
            }
        ]
    }

    try:
        requests.post(
            f"{BASE_URL}/api/v1/traces",
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=5,
        )
    except requests.RequestException:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
