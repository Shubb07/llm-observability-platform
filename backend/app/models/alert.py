import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

# Deliberately the same metric names AnalyticsMetrics already uses
# (app/schemas/analytics.py) rather than inventing a second vocabulary for
# the same numbers - a rule's `metric` is just "which field of the existing
# analytics computation to watch."
ALLOWED_METRICS = {
    "request_volume",
    "error_rate",
    "p50_latency_ms",
    "p95_latency_ms",
    "p99_latency_ms",
    "total_tokens",
    "total_cost",
}
ALLOWED_OPERATORS = {">", ">=", "<", "<="}
# Same set analytics.py's TIME_RANGES already supports - a rule's window is
# "how far back to compute the metric over," identical meaning to the
# dashboard's own analytics time-range picker.
ALLOWED_TIME_RANGES = {"24h", "7d", "30d"}


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    operator: Mapped[str] = mapped_column(String(2), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    time_range: Mapped[str] = mapped_column(String(10), nullable=False, default="24h")
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Edge-triggered notification state, not a timestamp-based cooldown: the
    # checker only POSTs a notification on the False->True transition, so a
    # rule that stays breached across many poll ticks fires once, not every
    # tick. Flips back to False once a check observes the metric back under
    # threshold, so a later re-breach notifies again.
    is_breached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    project: Mapped["Project"] = relationship()  # noqa: F821
