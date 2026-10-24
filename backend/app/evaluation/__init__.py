"""Evaluation engine - scores a trace's output against a set of named
evaluators, one Evaluation row per (trace, evaluator) pair.

run_heuristic_evaluators() is called synchronously right after a trace is
stored (see traces.py's ingest_traces). Per the HLD's reliability
constraint, an evaluator failing must never affect trace storage - each
evaluator is isolated in its own try/except, so one broken evaluator
produces a FAILED row for itself and doesn't stop the others or the
ingestion response.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.evaluation.heuristics import HEURISTIC_EVALUATORS
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
