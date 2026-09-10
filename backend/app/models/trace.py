import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Trace(Base):
    __tablename__ = "traces"
    __table_args__ = (
        # A client_trace_id is set by the SDK so a retried batch (e.g. after a
        # response is lost mid-flight) doesn't create a duplicate row. NULL is
        # exempt from the constraint in both Postgres and SQLite, so traces
        # ingested without one (manual API calls) are unaffected.
        UniqueConstraint("project_id", "client_trace_id", name="uq_trace_project_client_trace_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    client_trace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    model: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    completion: Mapped[str | None] = mapped_column(Text, nullable=True)

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[str] = mapped_column(String(20), default="success", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    tags: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    project: Mapped["Project"] = relationship()
