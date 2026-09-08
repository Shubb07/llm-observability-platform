"""Approximate per-token pricing for cost estimation.

These are best-effort snapshots, not billing-accurate figures — providers
change pricing over time and this table will drift. Treat `estimate_cost()`
as an estimate for the dashboard's cost trend, not an invoice. Update the
table below to match current provider pricing, or bypass it entirely by
passing `cost=` directly (see `manual.trace()`).

Unknown models return 0.0 rather than guessing.
"""

from __future__ import annotations

# model -> (input $ per 1K tokens, output $ per 1K tokens)
PRICING_PER_1K_TOKENS: dict[str, tuple[float, float]] = {
    "claude-opus-5": (0.005, 0.025),
    "claude-sonnet-5": (0.002, 0.010),
    "claude-haiku-4-5": (0.001, 0.005),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = PRICING_PER_1K_TOKENS.get(model)
    if pricing is None:
        return 0.0

    input_price_per_1k, output_price_per_1k = pricing
    return (prompt_tokens / 1000) * input_price_per_1k + (completion_tokens / 1000) * output_price_per_1k
