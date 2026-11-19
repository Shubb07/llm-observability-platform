from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_project_membership, require_admin
from app.core.db import get_db
from app.models.alert import ALLOWED_METRICS, ALLOWED_OPERATORS, ALLOWED_TIME_RANGES, AlertRule
from app.models.project import ProjectMembership
from app.schemas.alert import AlertRuleCreate, AlertRuleOut, AlertRuleUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["alerts"])


def _validate_rule_fields(metric: str, operator: str, time_range: str) -> None:
    if metric not in ALLOWED_METRICS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"metric must be one of {sorted(ALLOWED_METRICS)}")
    if operator not in ALLOWED_OPERATORS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"operator must be one of {sorted(ALLOWED_OPERATORS)}")
    if time_range not in ALLOWED_TIME_RANGES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"time_range must be one of {sorted(ALLOWED_TIME_RANGES)}")


@router.get("/{project_id}/alerts", response_model=list[AlertRuleOut])
def list_alert_rules(
    project_id: str,
    membership: ProjectMembership = Depends(get_project_membership),
    db: Session = Depends(get_db),
):
    return db.query(AlertRule).filter_by(project_id=project_id).order_by(AlertRule.created_at.desc()).all()


@router.post("/{project_id}/alerts", response_model=AlertRuleOut, status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    project_id: str,
    payload: AlertRuleCreate,
    _: ProjectMembership = Depends(require_admin),
    db: Session = Depends(get_db),
):
    _validate_rule_fields(payload.metric, payload.operator, payload.time_range)

    rule = AlertRule(
        project_id=project_id,
        name=payload.name,
        metric=payload.metric,
        operator=payload.operator,
        threshold=payload.threshold,
        time_range=payload.time_range,
        webhook_url=payload.webhook_url,
        is_active=payload.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{project_id}/alerts/{alert_id}", response_model=AlertRuleOut)
def update_alert_rule(
    project_id: str,
    alert_id: str,
    payload: AlertRuleUpdate,
    _: ProjectMembership = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule = db.query(AlertRule).filter_by(id=alert_id, project_id=project_id).first()
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert rule not found")

    updates = payload.model_dump(exclude_unset=True)
    _validate_rule_fields(
        updates.get("metric", rule.metric),
        updates.get("operator", rule.operator),
        updates.get("time_range", rule.time_range),
    )
    for field, value in updates.items():
        setattr(rule, field, value)

    # Any edit to the rule's actual condition invalidates whatever breach
    # state the checker last observed - without this, changing a rule from
    # (already-breached, no longer breached under the new condition) would
    # still read as breached until the next check tick happens to flip it,
    # and a rule edited back toward its old condition could skip notifying
    # on a real re-breach because is_breached was already True from before.
    if {"metric", "operator", "threshold", "time_range"} & updates.keys():
        rule.is_breached = False

    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{project_id}/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert_rule(
    project_id: str,
    alert_id: str,
    _: ProjectMembership = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule = db.query(AlertRule).filter_by(id=alert_id, project_id=project_id).first()
    if rule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert rule not found")
    db.delete(rule)
    db.commit()
