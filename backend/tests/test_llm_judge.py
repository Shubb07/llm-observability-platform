import json

import pytest

from app.evaluation.llm_judge import faithfulness, relevance


class FakeJudgeClient:
    """Never makes a real API call - just replays a scripted response, so
    relevance()'s parsing/validation logic is testable without a real
    Anthropic API key."""

    def __init__(self, response: str):
        self.response = response
        self.last_prompt: str | None = None

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def make_trace(prompt="What's the capital of France?", completion="Paris.", context=None):
    from app.models.trace import Trace

    return Trace(
        project_id="p1",
        model="gpt-4o",
        provider="openai",
        prompt=prompt,
        completion=completion,
        context=context,
        latency_ms=10.0,
        status="success",
    )


def test_relevance_parses_a_well_formed_judge_response():
    client = FakeJudgeClient(json.dumps({"score": 0.9, "reasoning": "Directly answers the question"}))
    outcome = relevance(make_trace(), client)

    assert outcome.score == 0.9
    assert outcome.reasoning == "Directly answers the question"


def test_relevance_includes_prompt_and_completion_in_the_judge_prompt():
    client = FakeJudgeClient(json.dumps({"score": 1.0, "reasoning": "fine"}))
    trace = make_trace(prompt="What's 2+2?", completion="4")

    relevance(trace, client)

    assert "What's 2+2?" in client.last_prompt
    assert "4" in client.last_prompt


def test_relevance_raises_on_malformed_json():
    client = FakeJudgeClient("not json at all")
    with pytest.raises(json.JSONDecodeError):
        relevance(make_trace(), client)


def test_relevance_raises_on_missing_score_field():
    client = FakeJudgeClient(json.dumps({"reasoning": "forgot the score"}))
    with pytest.raises(KeyError):
        relevance(make_trace(), client)


def test_relevance_raises_on_out_of_range_score():
    client = FakeJudgeClient(json.dumps({"score": 1.5, "reasoning": "overconfident"}))
    with pytest.raises(ValueError, match="out-of-range"):
        relevance(make_trace(), client)


def test_relevance_handles_null_completion():
    client = FakeJudgeClient(json.dumps({"score": 0.0, "reasoning": "no completion to judge"}))
    outcome = relevance(make_trace(completion=None), client)
    assert outcome.score == 0.0


def test_faithfulness_parses_a_well_formed_judge_response():
    client = FakeJudgeClient(json.dumps({"score": 0.8, "reasoning": "mostly supported by the context"}))
    trace = make_trace(context="Paris is the capital of France.")

    outcome = faithfulness(trace, client)

    assert outcome.score == 0.8
    assert outcome.reasoning == "mostly supported by the context"


def test_faithfulness_includes_context_and_completion_in_the_judge_prompt():
    client = FakeJudgeClient(json.dumps({"score": 1.0, "reasoning": "fine"}))
    trace = make_trace(completion="4", context="2+2=4")

    faithfulness(trace, client)

    assert "2+2=4" in client.last_prompt
    assert "4" in client.last_prompt


def test_faithfulness_raises_on_malformed_json():
    client = FakeJudgeClient("not json at all")
    with pytest.raises(json.JSONDecodeError):
        faithfulness(make_trace(context="some context"), client)


def test_faithfulness_raises_on_out_of_range_score():
    client = FakeJudgeClient(json.dumps({"score": -0.5, "reasoning": "overconfident"}))
    with pytest.raises(ValueError, match="out-of-range"):
        faithfulness(make_trace(context="some context"), client)


def test_faithfulness_skipped_when_context_is_none():
    client = FakeJudgeClient("should never be called")
    outcome = faithfulness(make_trace(context=None), client)

    assert outcome is None
    assert client.last_prompt is None


def test_faithfulness_skipped_when_context_is_empty_string():
    client = FakeJudgeClient("should never be called")
    outcome = faithfulness(make_trace(context=""), client)

    assert outcome is None
    assert client.last_prompt is None
