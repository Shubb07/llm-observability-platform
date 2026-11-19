from datetime import datetime

from pydantic import BaseModel


class AlertRuleCreate(BaseModel):
    name: str
    metric: str
    operator: str
    threshold: float
    time_range: str = "24h"
    webhook_url: str
    is_active: bool = True


class AlertRuleUpdate(BaseModel):
    # All optional - PATCH semantics, only the fields actually sent get
    # changed. Doesn't include project_id (a rule never moves projects) or
    # the is_breached/last_checked_at/last_triggered_at trio, which only the
    # checker job writes.
    name: str | None = None
    metric: str | None = None
    operator: str | None = None
    threshold: float | None = None
    time_range: str | None = None
    webhook_url: str | None = None
    is_active: bool | None = None


class AlertRuleOut(BaseModel):
    id: str
    project_id: str
    name: str
    metric: str
    operator: str
    threshold: float
    time_range: str
    webhook_url: str
    is_active: bool
    is_breached: bool
    last_checked_at: datetime | None
    last_triggered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
