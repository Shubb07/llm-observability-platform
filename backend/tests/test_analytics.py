from datetime import datetime, timedelta, timezone

import pytest

from app.models.trace import Trace


@pytest.fixture()
def project(client, auth_headers):
    response = client.post("/api/v1/projects", json={"name": "Analytics Project"}, headers=auth_headers)
    return response.json()


def test_requires_membership(client, project):
    other_payload = {"email": "outsider@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=other_payload)
    other_login = client.post("/api/v1/auth/login", json=other_payload).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    response = client.get(f"/api/v1/projects/{project['id']}/analytics", headers=other_headers)
    assert response.status_code == 403


def test_empty_project_returns_zeros(client, auth_headers, project):
    response = client.get(f"/api/v1/projects/{project['id']}/analytics", headers=auth_headers)

    assert response.status_code == 200
    overall = response.json()["overall"]
    assert overall == {
        "request_volume": 0,
        "error_rate": 0.0,
        "p50_latency_ms": 0.0,
        "p95_latency_ms": 0.0,
        "p99_latency_ms": 0.0,
        "total_tokens": 0,
        "total_cost": 0.0,
    }


def test_rejects_invalid_time_range(client, auth_headers, project):
    response = client.get(
        f"/api/v1/projects/{project['id']}/analytics",
        params={"time_range": "1y"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_computes_overall_metrics(client, auth_headers, project):
    payload = {
        "traces": [
            {"model": "gpt-4o", "provider": "openai", "prompt": "p", "latency_ms": ms, "status": s, "prompt_tokens": 10, "completion_tokens": 5, "cost": 0.01}
            for ms, s in [(10, "success"), (20, "success"), (30, "error"), (40, "success"), (50, "success")]
        ]
    }
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    response = client.get(f"/api/v1/projects/{project['id']}/analytics", headers=auth_headers)
    overall = response.json()["overall"]

    assert overall["request_volume"] == 5
    assert overall["error_rate"] == 0.2  # 1 error out of 5
    assert overall["p50_latency_ms"] == 30.0
    assert overall["p95_latency_ms"] == pytest.approx(48.0)
    assert overall["p99_latency_ms"] == pytest.approx(49.6)
    assert overall["total_tokens"] == 15 * 5
    assert overall["total_cost"] == pytest.approx(0.05)


def test_group_by_model_breaks_down_per_model(client, auth_headers, project):
    payload = {
        "traces": [
            {"model": "gpt-4o", "provider": "openai", "prompt": "p", "latency_ms": 100.0},
            {"model": "gpt-4o", "provider": "openai", "prompt": "p", "latency_ms": 200.0},
            {"model": "claude-sonnet-5", "provider": "anthropic", "prompt": "p", "latency_ms": 50.0},
        ]
    }
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    response = client.get(
        f"/api/v1/projects/{project['id']}/analytics",
        params={"group_by": "model"},
        headers=auth_headers,
    )
    by_model = {b["model"]: b for b in response.json()["by_model"]}

    assert by_model["gpt-4o"]["request_volume"] == 2
    assert by_model["claude-sonnet-5"]["request_volume"] == 1


def test_time_range_excludes_old_traces(client, auth_headers, project, db_session):
    old_trace = Trace(
        project_id=project["id"],
        model="gpt-4o",
        provider="openai",
        prompt="old",
        latency_ms=100.0,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=10),
    )
    db_session.add(old_trace)
    db_session.commit()

    within_range = client.get(
        f"/api/v1/projects/{project['id']}/analytics", params={"time_range": "24h"}, headers=auth_headers
    )
    assert within_range.json()["overall"]["request_volume"] == 0

    wider_range = client.get(
        f"/api/v1/projects/{project['id']}/analytics", params={"time_range": "30d"}, headers=auth_headers
    )
    assert wider_range.json()["overall"]["request_volume"] == 1
