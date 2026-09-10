import pytest


@pytest.fixture()
def project(client, auth_headers):
    response = client.post(
        "/api/v1/projects", json={"name": "Trace Project"}, headers=auth_headers
    )
    return response.json()


def test_ingest_traces_requires_api_key(client):
    response = client.post(
        "/api/v1/traces",
        json={"traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 120.5}]},
    )
    assert response.status_code == 401


def test_ingest_traces_rejects_invalid_api_key(client):
    response = client.post(
        "/api/v1/traces",
        json={"traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 120.5}]},
        headers={"X-API-Key": "not-a-real-key"},
    )
    assert response.status_code == 401


def test_ingest_traces_stores_batch(client, project):
    payload = {
        "traces": [
            {
                "model": "gpt-4o",
                "provider": "openai",
                "prompt": "Summarize this document",
                "completion": "Here is a summary.",
                "prompt_tokens": 42,
                "completion_tokens": 8,
                "latency_ms": 350.2,
                "cost": 0.0012,
                "status": "success",
                "tags": {"env": "prod"},
            },
            {
                "model": "gpt-4o",
                "provider": "openai",
                "prompt": "Bad call",
                "latency_ms": 12.0,
                "status": "error",
                "error_message": "rate limited",
            },
        ]
    }

    response = client.post(
        "/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]}
    )

    assert response.status_code == 201
    assert response.json()["ingested"] == 2


def test_ingest_traces_is_idempotent_on_client_trace_id(client, auth_headers, project):
    payload = {
        "traces": [
            {
                "model": "gpt-4o",
                "provider": "openai",
                "prompt": "hi",
                "latency_ms": 100.0,
                "client_trace_id": "fixed-retry-id-1",
            }
        ]
    }

    first = client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})
    assert first.status_code == 201
    assert first.json() == {"ingested": 1, "skipped_duplicates": 0}

    # Simulates the SDK retrying the same batch after a lost response.
    retry = client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})
    assert retry.status_code == 201
    assert retry.json() == {"ingested": 0, "skipped_duplicates": 1}

    listed = client.get(f"/api/v1/projects/{project['id']}/traces", headers=auth_headers)
    assert listed.json()["total"] == 1


def test_ingest_traces_without_client_trace_id_is_not_deduplicated(client, auth_headers, project):
    payload = {"traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 100.0}]}

    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    listed = client.get(f"/api/v1/projects/{project['id']}/traces", headers=auth_headers)
    assert listed.json()["total"] == 2


def test_list_traces_filters_by_status(client, auth_headers, project):
    payload = {
        "traces": [
            {"model": "gpt-4o", "provider": "openai", "prompt": "ok", "latency_ms": 100.0, "status": "success"},
            {"model": "gpt-4o", "provider": "openai", "prompt": "bad", "latency_ms": 50.0, "status": "error"},
        ]
    }
    client.post("/api/v1/traces", json=payload, headers={"X-API-Key": project["api_key"]})

    response = client.get(
        f"/api/v1/projects/{project['id']}/traces",
        params={"status": "error"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["status"] == "error"


def test_list_traces_requires_membership(client, project):
    other_payload = {"email": "viewer@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=other_payload)
    other_login = client.post("/api/v1/auth/login", json=other_payload).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    response = client.get(f"/api/v1/projects/{project['id']}/traces", headers=other_headers)

    assert response.status_code == 403


def test_get_single_trace_not_found(client, auth_headers, project):
    response = client.get(
        f"/api/v1/projects/{project['id']}/traces/does-not-exist",
        headers=auth_headers,
    )
    assert response.status_code == 404
