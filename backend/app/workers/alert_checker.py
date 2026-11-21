from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.api.analytics import TIME_RANGES, _compute_metrics
from app.models.alert import AlertRule
from app.models.trace import Trace

OPERATORS = {
    ">": lambda value, threshold: value > threshold,
    ">=": lambda value, threshold: value >= threshold,
    "<": lambda value, threshold: value < threshold,
    "<=": lambda value, threshold: value <= threshold,
}


def _metric_value(db: Session, rule: AlertRule) -> float:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - TIME_RANGES[rule.time_range]
    traces = (
        db.query(Trace)
        .filter(Trace.project_id == rule.project_id, Trace.created_at >= since)
        .all()
    )
    metrics = _compute_metrics(traces)
    return getattr(metrics, rule.metric)


def _send_webhook(rule: AlertRule, value: float) -> None:
    payload = {
        "alert_rule_id": rule.id,
        "project_id": rule.project_id,
        "name": rule.name,
        "metric": rule.metric,
        "operator": rule.operator,
        "threshold": rule.threshold,
        "value": value,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        httpx.post(rule.webhook_url, json=payload, timeout=5)
    except httpx.HTTPError:
        # A broken/unreachable webhook endpoint must never stop the checker
        # from evaluating the rest of this project's rules, or the next
        # project's - same "never let one failure take down the whole run"
        # principle the evaluation engine already follows for evaluators.
        pass


def check_alert_rules(db: Session) -> None:
    """Evaluate every active rule's metric against its threshold and notify
    on breach. Edge-triggered, not level-triggered: a rule that's already
    is_breached only re-notifies once it's observed back under threshold and
    breaches again - called on a fixed interval (see the scheduler wired up
    in main.py), so a rule that stays breached across many ticks fires the
    webhook once, not every tick."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for rule in db.query(AlertRule).filter_by(is_active=True).all():
        value = _metric_value(db, rule)
        breached = OPERATORS[rule.operator](value, rule.threshold)

        rule.last_checked_at = now
        if breached and not rule.is_breached:
            rule.last_triggered_at = now
            _send_webhook(rule, value)
        rule.is_breached = breached

    db.commit()
