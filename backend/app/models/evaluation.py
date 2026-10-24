import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class EvaluationStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Evaluation(Base):
    """One evaluator's result against one trace. A trace can have several -
    one row per (trace, evaluator) pair, not one row per trace, so adding a
    new evaluator later doesn't require touching existing rows and a single
    evaluator failing doesn't block or invalidate the others' results.

    "Show your work" (PRD product principle): every score carries the
    evaluator that produced it and a human-readable reason, not just a bare
    number - evaluator_name + reasoning together are what make a score
    auditable instead of an unexplained float.
    """

    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id: Mapped[str] = mapped_column(ForeignKey("traces.id"), nullable=False, index=True)

    evaluator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=EvaluationStatus.PENDING.value, index=True)

    # 0.0-1.0, null until the evaluator actually runs (or if it fails before
    # producing one). Kept as a plain float rather than a pass/fail bool so a
    # future LLM-as-judge evaluator can report a graded score, not just a
    # binary verdict - heuristic evaluators below just use 0.0 or 1.0.
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    trace: Mapped["Trace"] = relationship()
