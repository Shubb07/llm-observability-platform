import pytest


@pytest.fixture()
def project(client, auth_headers):
    response = client.post("/api/v1/projects", json={"name": "Alerting Project"}, headers=auth_headers)
    return response.json()


@pytest.fixture()
def viewer_headers(client, auth_headers, project):
    payload = {"email": "viewer@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)
    login = client.post("/api/v1/auth/login", json=payload).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": payload["email"], "role": "VIEWER"},
        headers=auth_headers,
    )
    return headers


def _make_rule_payload(**overrides):
    payload = {
        "name": "High error rate",
        "metric": "error_rate",
        "operator": ">",
        "threshold": 0.1,
        "time_range": "24h",
        "webhook_url": "https://example.com/hooks/alert",
    }
    payload.update(overrides)
    return payload


def test_admin_can_create_alert_rule(client, auth_headers, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "High error rate"
    assert body["is_active"] is True
    assert body["is_breached"] is False
    assert body["last_triggered_at"] is None


def test_non_admin_cannot_create_alert_rule(client, project, viewer_headers):
    response = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=viewer_headers
    )
    assert response.status_code == 403


def test_create_rejects_unknown_metric(client, auth_headers, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/alerts",
        json=_make_rule_payload(metric="not_a_real_metric"),
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_rejects_unknown_operator(client, auth_headers, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/alerts",
        json=_make_rule_payload(operator="=="),
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_rejects_unknown_time_range(client, auth_headers, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/alerts",
        json=_make_rule_payload(time_range="1h"),
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_alert_rules_visible_to_any_member(client, auth_headers, project, viewer_headers):
    client.post(f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers)

    response = client.get(f"/api/v1/projects/{project['id']}/alerts", headers=viewer_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_admin_can_update_alert_rule(client, auth_headers, project):
    rule = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers
    ).json()

    response = client.patch(
        f"/api/v1/projects/{project['id']}/alerts/{rule['id']}",
        json={"threshold": 0.25, "is_active": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["threshold"] == 0.25
    assert body["is_active"] is False
    assert body["name"] == "High error rate"  # untouched field unchanged


def test_updating_the_condition_resets_breach_state(client, auth_headers, project, db_session):
    from app.models.alert import AlertRule

    rule = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers
    ).json()

    # Simulate the checker having already flagged this rule as breached.
    db_row = db_session.query(AlertRule).filter_by(id=rule["id"]).first()
    db_row.is_breached = True
    db_session.commit()

    response = client.patch(
        f"/api/v1/projects/{project['id']}/alerts/{rule['id']}",
        json={"threshold": 0.9},
        headers=auth_headers,
    )

    assert response.json()["is_breached"] is False


def test_update_rejects_unknown_metric(client, auth_headers, project):
    rule = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers
    ).json()

    response = client.patch(
        f"/api/v1/projects/{project['id']}/alerts/{rule['id']}",
        json={"metric": "not_a_real_metric"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_update_not_found(client, auth_headers, project):
    response = client.patch(
        f"/api/v1/projects/{project['id']}/alerts/does-not-exist",
        json={"threshold": 0.5},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_non_admin_cannot_update_alert_rule(client, auth_headers, project, viewer_headers):
    rule = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers
    ).json()

    response = client.patch(
        f"/api/v1/projects/{project['id']}/alerts/{rule['id']}",
        json={"threshold": 0.5},
        headers=viewer_headers,
    )
    assert response.status_code == 403


def test_admin_can_delete_alert_rule(client, auth_headers, project):
    rule = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers
    ).json()

    response = client.delete(f"/api/v1/projects/{project['id']}/alerts/{rule['id']}", headers=auth_headers)
    assert response.status_code == 204

    listed = client.get(f"/api/v1/projects/{project['id']}/alerts", headers=auth_headers).json()
    assert listed == []


def test_non_admin_cannot_delete_alert_rule(client, auth_headers, project, viewer_headers):
    rule = client.post(
        f"/api/v1/projects/{project['id']}/alerts", json=_make_rule_payload(), headers=auth_headers
    ).json()

    response = client.delete(f"/api/v1/projects/{project['id']}/alerts/{rule['id']}", headers=viewer_headers)
    assert response.status_code == 403


def test_delete_not_found(client, auth_headers, project):
    response = client.delete(f"/api/v1/projects/{project['id']}/alerts/does-not-exist", headers=auth_headers)
    assert response.status_code == 404
