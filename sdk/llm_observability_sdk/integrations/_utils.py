from __future__ import annotations

from typing import Any


def render_messages(messages: list[dict[str, Any]]) -> str:
    """Flatten a chat-style messages list into a single string for the
    `prompt` field. Traces store the whole exchange as text — structured
    per-message storage is future work if the dashboard needs it."""
    return "\n".join(f"{m.get('role', '?')}: {m.get('content', '')}" for m in messages)
