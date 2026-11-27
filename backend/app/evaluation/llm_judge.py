"""LLM-as-judge evaluation - the half of the evaluation engine that
genuinely needs a model call, unlike heuristics.py's regex-only checks.

`relevance()` and `faithfulness()` are wired into ingestion (see
app/evaluation/__init__.py's run_llm_judge_evaluators, called from
traces.py's ingest_traces) and run synchronously, inline, right after the
heuristic evaluators - a deliberate shortcut rather than the HLD's intended
design. The HLD calls for this to run asynchronously via a background job
queue (APScheduler polling PENDING Evaluation rows), specifically because
an LLM call is too slow and too unreliable to run inline during ingestion.
Running it inline was chosen anyway to get a working, demoable judge
evaluator without first building that queue; revisit if ingestion volume
or latency makes the queue worth it.

`faithfulness()` scores whether trace.completion is grounded in
trace.context (the retrieved documents for a RAG-style call). It's skipped
entirely - not run, no FAILED row - when trace.context is None/empty,
since there's nothing to check groundedness against.
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


FAITHFULNESS_PROMPT_TEMPLATE = """You are evaluating whether an AI assistant's response is faithful to (i.e. \
grounded in and supported by) a given context.

Context:
{context}

Response:
{completion}

Rate how well the response is grounded in the context, from 0.0 (not \
supported by the context at all, e.g. fabricated or contradicted) to 1.0 \
(fully supported by the context). Respond with ONLY a JSON object and \
nothing else, in exactly this shape: \
{{"score": <float 0.0-1.0>, "reasoning": "<one sentence>"}}"""


class JudgeClient(Protocol):
    """Whatever can take a prompt and return a model's text response. A
    Protocol rather than a concrete class so relevance() can be tested
    against a fake that never makes a real API call."""

    def complete(self, prompt: str) -> str: ...


class AnthropicJudgeClient:
    """The real client - thin wrapper over the Anthropic SDK. Takes its API
    key directly rather than reading settings itself; the caller
    (run_llm_judge_evaluators) is the one that reads settings.anthropic_api_key
    and passes it in, so this class stays trivially testable with a fake key.
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


def faithfulness(trace: Trace, client: JudgeClient) -> EvaluationOutcome | None:
    """Asks the judge model to score how well trace.completion is grounded
    in trace.context. Returns None - meaning "skip, don't score" - when
    trace.context is None/empty, since there's nothing to check
    groundedness against; the caller is expected to treat None as "don't
    write an Evaluation row at all", not as a failure. Otherwise, same
    contract as relevance(): raises on a malformed or out-of-range judge
    response rather than guessing a score."""
    if not trace.context:
        return None

    prompt = FAITHFULNESS_PROMPT_TEMPLATE.format(context=trace.context, completion=trace.completion or "")
    raw = client.complete(prompt)

    data = json.loads(raw)
    score = float(data["score"])
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Judge returned an out-of-range score: {score}")

    return EvaluationOutcome(score=score, reasoning=str(data.get("reasoning", "")))
