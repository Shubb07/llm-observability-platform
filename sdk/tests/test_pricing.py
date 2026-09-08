from llm_observability_sdk.pricing import estimate_cost


def test_known_model_cost_matches_manual_calculation():
    # claude-sonnet-5: $0.002/1K input, $0.010/1K output
    cost = estimate_cost("claude-sonnet-5", prompt_tokens=1000, completion_tokens=500)
    assert cost == 0.002 * 1 + 0.010 * 0.5


def test_zero_tokens_costs_nothing():
    assert estimate_cost("claude-opus-5", prompt_tokens=0, completion_tokens=0) == 0.0


def test_unknown_model_returns_zero_rather_than_guessing():
    assert estimate_cost("some-future-model", prompt_tokens=1000, completion_tokens=1000) == 0.0
