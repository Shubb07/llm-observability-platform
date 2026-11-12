"""LLM-as-judge evaluation - the half of the evaluation engine that
genuinely needs a model call, unlike heuristics.py's regex-only checks.

Scope of this first piece, deliberately: just `relevance()` as a pure,
testable function plus a real client to back it. NOT included yet, on
purpose - each is its own next chunk, not bundled in here:
  - Wiring this into ingest_traces or any scheduler. An LLM call is too
    slow to run inline during ingestion (the reason the HLD splits
    evaluation into a synchronous heuristic phase and an async
    LLM-as-judge phase in the first place) - this needs a background job
    queue (APScheduler polling PENDING Evaluation rows), not a direct call
    from the request path.
  - `faithfulness`, the other LLM-as-judge evaluator the PRD names
    (US-005). Faithfulness means "is the completion grounded in the
    context it was supposed to use" - that requires a context/retrieved-
    document field the Trace model doesn't have. Building a faithfulness
    evaluator without something to check faithfulness against would be
    scoring against nothing; that's a schema decision to make deliberately,
    not improvise here.
  - Settings/env wiring for a real API key - AnthropicJudgeClient takes
    one as a constructor argument rather than reading it from app
    settings, since nothing calls it yet.
"""

from __future__ import annotations

import json
from typing import Protocol

from app.evaluation.heuristics import EvaluationOutcome
from app.models.trace import Trace

RELEVANCE_PROMPT_TEMPLATE = """You are evaluating whether an AI assistant's response is relevant to what was asked.

Prompt:
{prompt}

Response:
{completion}

Rate how relevant the response is to the prompt, from 0.0 (completely \
off-topic) to 1.0 (fully relevant and on-topic). Respond with ONLY a JSON \
object and nothing else, in exactly this shape: \
{{"score": <float 0.0-1.0>, "reasoning": "<one sentence>"}}"""


class JudgeClient(Protocol):
    """Whatever can take a prompt and return a model's text response. A
    Protocol rather than a concrete class so relevance() can be tested
    against a fake that never makes a real API call."""

    def complete(self, prompt: str) -> str: ...


class AnthropicJudgeClient:
    """The real client - thin wrapper over the Anthropic SDK. Takes its API
    key directly rather than reading settings, since nothing constructs
    this yet outside tests; wiring it up to run for real is a later chunk.
    """

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5") -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text"))


def relevance(trace: Trace, client: JudgeClient) -> EvaluationOutcome:
    """Asks the judge model to score how relevant trace.completion is to
    trace.prompt. Raises (ValueError, via json.loads/KeyError) on a
    malformed or out-of-range response rather than guessing a score -
    the caller (the same orchestrator heuristics already run through)
    catches that and records a FAILED row, same as any other evaluator
    failure."""
    prompt = RELEVANCE_PROMPT_TEMPLATE.format(prompt=trace.prompt, completion=trace.completion or "")
    raw = client.complete(prompt)

    data = json.loads(raw)
    score = float(data["score"])
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Judge returned an out-of-range score: {score}")

    return EvaluationOutcome(score=score, reasoning=str(data.get("reasoning", "")))
