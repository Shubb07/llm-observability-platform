from pydantic import BaseModel


class AnalyticsMetrics(BaseModel):
    request_volume: int
    error_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_tokens: int
    total_cost: float


class ModelBreakdown(AnalyticsMetrics):
    model: str


class AnalyticsOut(BaseModel):
    time_range: str
    overall: AnalyticsMetrics
    by_model: list[ModelBreakdown] | None = None
