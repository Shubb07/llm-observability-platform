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
    # instrument_openai() resolves to these exact model strings via the
    # API response's `response.model` - without entries here, every
    # OpenAI-traced call silently recorded cost=0.0 regardless of usage.
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.010, 0.030),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "gemini-3.8-flash": (0.0001, 0.0004),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = PRICING_PER_1K_TOKENS.get(model)
    if pricing is None:
        return 0.0

    input_price_per_1k, output_price_per_1k = pricing
    return (prompt_tokens / 1000) * input_price_per_1k + (completion_tokens / 1000) * output_price_per_1k
