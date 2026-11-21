from datetime import datetime, timezone

import pytest

from app.models.alert import AlertRule
from app.models.trace import Trace
from app.workers.alert_checker import check_alert_rules


@pytest.fixture()
def project(client, auth_headers):
    response = client.post("/api/v1/projects", json={"name": "Checker Project"}, headers=auth_headers)
    return response.json()


def _make_rule(db_session, project_id, **overrides):
    defaults = dict(
        project_id=project_id,
        name="Error rate too high",
        metric="error_rate",
        operator=">",
        threshold=0.1,
        time_range="24h",
        webhook_url="https://example.com/hook",
        is_active=True,
    )
    defaults.update(overrides)
    rule = AlertRule(**defaults)
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


def _make_trace(db_session, project_id, status="success"):
    trace = Trace(
        project_id=project_id,
        model="gpt-4o",
        provider="openai",
        prompt="hi",
        latency_ms=100.0,
        status=status,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db_session.add(trace)
    db_session.commit()
    return trace


def test_rule_flips_to_breached_and_sends_webhook(db_session, project, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.workers.alert_checker.httpx.post",
        lambda url, json, timeout: sent.append((url, json)),
    )

    for _ in range(3):
        _make_trace(db_session, project["id"], status="error")
    rule = _make_rule(db_session, project["id"])

    check_alert_rules(db_session)
    db_session.refresh(rule)

    assert rule.is_breached is True
    assert rule.last_triggered_at is not None
    assert rule.last_checked_at is not None
    assert len(sent) == 1
    assert sent[0][0] == "https://example.com/hook"
    assert sent[0][1]["metric"] == "error_rate"


def test_does_not_resend_webhook_while_still_breached(db_session, project, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.workers.alert_checker.httpx.post",
        lambda url, json, timeout: sent.append((url, json)),
    )

    for _ in range(3):
        _make_trace(db_session, project["id"], status="error")
    rule = _make_rule(db_session, project["id"])

    check_alert_rules(db_session)
    check_alert_rules(db_session)
    check_alert_rules(db_session)
    db_session.refresh(rule)

    assert rule.is_breached is True
    assert len(sent) == 1  # edge-triggered - not one per tick


def test_clears_and_can_refire_after_recovering(db_session, project, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.workers.alert_checker.httpx.post",
        lambda url, json, timeout: sent.append((url, json)),
    )

    for _ in range(3):
        _make_trace(db_session, project["id"], status="error")
    rule = _make_rule(db_session, project["id"])
    check_alert_rules(db_session)
    db_session.refresh(rule)
    assert rule.is_breached is True

    # Recovery: enough new successful traces to push error_rate back under
    # the threshold within the same time window.
    for _ in range(30):
        _make_trace(db_session, project["id"], status="success")
    check_alert_rules(db_session)
    db_session.refresh(rule)
    assert rule.is_breached is False
    assert len(sent) == 1  # still just the one from the original breach

    for _ in range(3):
        _make_trace(db_session, project["id"], status="error")
    check_alert_rules(db_session)
    db_session.refresh(rule)
    assert rule.is_breached is True
    assert len(sent) == 2  # re-fired on the new breach


def test_inactive_rule_is_skipped(db_session, project, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.workers.alert_checker.httpx.post",
        lambda url, json, timeout: sent.append((url, json)),
    )

    for _ in range(3):
        _make_trace(db_session, project["id"], status="error")
    rule = _make_rule(db_session, project["id"], is_active=False)

    check_alert_rules(db_session)
    db_session.refresh(rule)

    assert rule.is_breached is False
    assert rule.last_checked_at is None
    assert sent == []


def test_webhook_failure_does_not_crash_the_checker(db_session, project, monkeypatch):
    import httpx as httpx_module

    def _raise(*args, **kwargs):
        raise httpx_module.ConnectError("refused")

    monkeypatch.setattr("app.workers.alert_checker.httpx.post", _raise)

    for _ in range(3):
        _make_trace(db_session, project["id"], status="error")
    rule = _make_rule(db_session, project["id"])

    check_alert_rules(db_session)  # must not raise
    db_session.refresh(rule)

    assert rule.is_breached is True
    assert rule.last_triggered_at is not None
