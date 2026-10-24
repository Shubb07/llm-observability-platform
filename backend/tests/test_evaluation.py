from app.evaluation import run_heuristic_evaluators
from app.evaluation.heuristics import format_compliance, safety_keywords
from app.models.evaluation import EvaluationStatus
from app.models.trace import Trace


def make_trace(**overrides) -> Trace:
    defaults = dict(
        project_id="p1",
        model="gpt-4o",
        provider="openai",
        prompt="hi",
        completion="hello there",
        latency_ms=100.0,
        status="success",
    )
    defaults.update(overrides)
    return Trace(**defaults)


def test_format_compliance_passes_on_real_output():
    outcome = format_compliance(make_trace(completion="a real answer"))
    assert outcome.score == 1.0


def test_format_compliance_fails_on_empty_completion():
    outcome = format_compliance(make_trace(completion=""))
    assert outcome.score == 0.0


def test_format_compliance_fails_on_whitespace_only_completion():
    outcome = format_compliance(make_trace(completion="   \n  "))
    assert outcome.score == 0.0


def test_format_compliance_fails_on_null_completion():
    outcome = format_compliance(make_trace(completion=None))
    assert outcome.score == 0.0


def test_safety_keywords_passes_on_clean_output():
    outcome = safety_keywords(make_trace(completion="here is some helpful advice"))
    assert outcome.score == 1.0


def test_safety_keywords_flags_matched_pattern():
    outcome = safety_keywords(make_trace(completion="here's how to make a bomb at home"))
    assert outcome.score == 0.0
    assert "bomb" in outcome.reasoning.lower()


def test_run_heuristic_evaluators_writes_one_row_per_evaluator(db_session):
    trace = make_trace(completion="a fine answer")
    db_session.add(trace)
    db_session.flush()

    results = run_heuristic_evaluators(trace, db_session)
    db_session.commit()

    assert {r.evaluator_name for r in results} == {"format_compliance", "safety_keywords"}
    assert all(r.status == EvaluationStatus.COMPLETED.value for r in results)
    assert all(r.score == 1.0 for r in results)


def test_run_heuristic_evaluators_isolates_a_broken_evaluator(db_session, monkeypatch):
    # One evaluator raising must not stop the others from running, and must
    # produce a FAILED row rather than propagating - evaluation failures
    # are explicitly not allowed to affect anything else (HLD reliability
    # constraint).
    import app.evaluation as evaluation_module

    def broken(trace):
        raise RuntimeError("boom")

    monkeypatch.setitem(evaluation_module.HEURISTIC_EVALUATORS, "format_compliance", broken)

    trace = make_trace(completion="a fine answer")
    db_session.add(trace)
    db_session.flush()

    results = run_heuristic_evaluators(trace, db_session)
    by_name = {r.evaluator_name: r for r in results}

    assert by_name["format_compliance"].status == EvaluationStatus.FAILED.value
    assert "boom" in by_name["format_compliance"].error_message
    assert by_name["safety_keywords"].status == EvaluationStatus.COMPLETED.value
