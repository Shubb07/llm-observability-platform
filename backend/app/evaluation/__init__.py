"""Evaluation engine - scores a trace's output against a set of named
evaluators, one Evaluation row per (trace, evaluator) pair.

run_heuristic_evaluators() and run_llm_judge_evaluators() are both called
synchronously right after a trace is stored (see traces.py's
ingest_traces). Per the HLD's reliability constraint, an evaluator failing
must never affect trace storage - each evaluator is isolated in its own
try/except, so one broken evaluator produces a FAILED row for itself and
doesn't stop the others or the ingestion response.

Running the LLM-as-judge evaluator inline (rather than via the background
job queue the HLD calls for) is a deliberate shortcut, not the final
design - it adds real per-request latency and only scales as far as
ingestion traffic stays low. Tracked as a known simplification to revisit
if/when ingestion volume or latency makes it worth building the async
queue.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.evaluation.heuristics import HEURISTIC_EVALUATORS
from app.evaluation.llm_judge import AnthropicJudgeClient, relevance
from app.models.evaluation import Evaluation, EvaluationStatus
from app.models.trace import Trace


def run_heuristic_evaluators(trace: Trace, db: Session) -> list[Evaluation]:
    results: list[Evaluation] = []
    for name, evaluator in HEURISTIC_EVALUATORS.items():
        try:
            outcome = evaluator(trace)
            evaluation = Evaluation(
                trace_id=trace.id,
                evaluator_name=name,
                status=EvaluationStatus.COMPLETED.value,
                score=outcome.score,
                reasoning=outcome.reasoning,
            )
        except Exception as exc:
            evaluation = Evaluation(
                trace_id=trace.id,
                evaluator_name=name,
                status=EvaluationStatus.FAILED.value,
                error_message=str(exc),
            )
        db.add(evaluation)
        results.append(evaluation)
    return results


def run_llm_judge_evaluators(trace: Trace, db: Session) -> list[Evaluation]:
    """Mirrors run_heuristic_evaluators' isolation guarantee. No-ops (returns
    an empty list, adds nothing) when no API key is configured, so
    environments without one - tests, local dev without a key - behave
    exactly as before this was wired in."""
    if not settings.anthropic_api_key:
        return []

    client = AnthropicJudgeClient(api_key=settings.anthropic_api_key)
    try:
        outcome = relevance(trace, client)
        evaluation = Evaluation(
            trace_id=trace.id,
            evaluator_name="relevance",
            status=EvaluationStatus.COMPLETED.value,
            score=outcome.score,
            reasoning=outcome.reasoning,
        )
    except Exception as exc:
        evaluation = Evaluation(
            trace_id=trace.id,
            evaluator_name="relevance",
            status=EvaluationStatus.FAILED.value,
            error_message=str(exc),
        )
    db.add(evaluation)
    return [evaluation]
