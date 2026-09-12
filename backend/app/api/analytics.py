from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_project_membership
from app.core.db import get_db
from app.models.project import ProjectMembership
from app.models.trace import Trace
from app.schemas.analytics import AnalyticsMetrics, AnalyticsOut, ModelBreakdown

router = APIRouter(prefix="/api/v1", tags=["analytics"])

TIME_RANGES = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile via linear interpolation. Pure Python because
    percentile aggregates aren't portable across Postgres (has them) and
    SQLite (doesn't) - traded a query for simplicity, fine at this scale."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = (len(sorted_values) - 1) * pct
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    if lower == upper:
        return sorted_values[lower]

    lower_weight = upper - rank
    upper_weight = rank - lower
    return sorted_values[lower] * lower_weight + sorted_values[upper] * upper_weight


def _compute_metrics(traces: list[Trace]) -> AnalyticsMetrics:
    if not traces:
        return AnalyticsMetrics(
            request_volume=0,
            error_rate=0.0,
            p50_latency_ms=0.0,
            p95_latency_ms=0.0,
            p99_latency_ms=0.0,
            total_tokens=0,
            total_cost=0.0,
        )

    latencies = sorted(t.latency_ms for t in traces)
    error_count = sum(1 for t in traces if t.status == "error")

    return AnalyticsMetrics(
        request_volume=len(traces),
        error_rate=error_count / len(traces),
        p50_latency_ms=_percentile(latencies, 0.50),
        p95_latency_ms=_percentile(latencies, 0.95),
        p99_latency_ms=_percentile(latencies, 0.99),
        total_tokens=sum(t.prompt_tokens + t.completion_tokens for t in traces),
        total_cost=sum(t.cost for t in traces),
    )


@router.get("/projects/{project_id}/analytics", response_model=AnalyticsOut)
def get_analytics(
    project_id: str,
    time_range: str = Query(default="24h"),
    model: str | None = Query(default=None),
    group_by: str | None = Query(default=None),
    membership: ProjectMembership = Depends(get_project_membership),
    db: Session = Depends(get_db),
):
    if time_range not in TIME_RANGES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"time_range must be one of {sorted(TIME_RANGES)}",
        )
    if group_by not in (None, "model"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "group_by must be 'model' if set")

    # created_at is stored as a naive UTC timestamp (see Trace model), so the
    # cutoff must be naive too - comparing aware vs. naive datetimes is a
    # driver-dependent landmine across SQLite (tests) and Postgres (prod).
    since = datetime.now(timezone.utc).replace(tzinfo=None) - TIME_RANGES[time_range]

    query = db.query(Trace).filter(Trace.project_id == project_id, Trace.created_at >= since)
    if model is not None:
        query = query.filter(Trace.model == model)

    traces = query.all()
    overall = _compute_metrics(traces)

    by_model = None
    if group_by == "model":
        grouped: dict[str, list[Trace]] = {}
        for t in traces:
            grouped.setdefault(t.model, []).append(t)
        by_model = [
            ModelBreakdown(model=name, **_compute_metrics(items).model_dump())
            for name, items in grouped.items()
        ]

    return AnalyticsOut(time_range=time_range, overall=overall, by_model=by_model)
