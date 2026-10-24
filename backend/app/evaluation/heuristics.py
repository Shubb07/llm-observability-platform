"""Heuristic (format/regex) evaluators - the synchronous, no-LLM-call half
of the evaluation engine (HLD's phase 5a). These run inline right after a
trace is stored, so they're intentionally cheap: no network calls, no
external API, nothing that could meaningfully slow down ingestion.

What's NOT here on purpose: relevance and faithfulness, the other two
built-in evaluators the PRD names (US-005), genuinely need an LLM to judge
whether a completion is relevant to its prompt or faithful to retrieved
context - that's not a regex problem. Those are LLM-as-judge evaluators,
meant to run asynchronously (HLD's phase 5b, via a scheduler polling
PENDING jobs) precisely because an LLM call is too slow and too unreliable
to run inline during ingestion. Not built yet.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from app.models.trace import Trace

# Deliberately small and conservative: a short list of unambiguous terms
# rather than an attempt at comprehensive content moderation. A real safety
# evaluator belongs in the LLM-as-judge tier (nuance, context, severity) -
# this one exists to catch the obvious, cheap-to-catch cases inline, not to
# be the platform's actual safety net.
_FLAGGED_PATTERNS = [
    re.compile(r"\bkill (yourself|urself)\b", re.IGNORECASE),
    re.compile(r"\bhow to (make|build) a bomb\b", re.IGNORECASE),
    re.compile(r"\bi hate (all )?(jews|muslims|black people|women|gay people)\b", re.IGNORECASE),
]


@dataclass
class EvaluationOutcome:
    score: float  # 0.0-1.0
    reasoning: str


def format_compliance(trace: Trace) -> EvaluationOutcome:
    """A successful call should actually have output. Catches the case
    where status="success" was reported but completion is empty, null, or
    just whitespace - a real, if basic, format problem worth surfacing
    rather than letting it blend into traces that look otherwise fine."""
    completion = (trace.completion or "").strip()
    if not completion:
        return EvaluationOutcome(score=0.0, reasoning="Completion is empty despite a successful status")
    return EvaluationOutcome(score=1.0, reasoning="Completion is non-empty")


def safety_keywords(trace: Trace) -> EvaluationOutcome:
    """Flags completions matching an explicit, narrow denylist. See the
    module docstring for why this is deliberately minimal rather than a
    real content-safety system."""
    completion = trace.completion or ""
    for pattern in _FLAGGED_PATTERNS:
        if pattern.search(completion):
            return EvaluationOutcome(
                score=0.0, reasoning=f"Completion matches a flagged pattern: {pattern.pattern!r}"
            )
    return EvaluationOutcome(score=1.0, reasoning="No flagged patterns found")


# Registry the orchestrator in __init__.py iterates - add a new heuristic
# evaluator here and it's automatically run for every future trace.
HEURISTIC_EVALUATORS: dict[str, Callable[[Trace], EvaluationOutcome]] = {
    "format_compliance": format_compliance,
    "safety_keywords": safety_keywords,
}
