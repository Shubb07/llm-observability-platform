def test_create_project_returns_api_key(client, auth_headers):
    response = client.post(
        "/api/v1/projects", json={"name": "My Project"}, headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "My Project"
    assert body["status"] == "ACTIVE"
    assert body["api_key"].startswith("llmobs_")


def test_create_project_requires_auth(client):
    response = client.post("/api/v1/projects", json={"name": "No Auth"})
    assert response.status_code == 401


def test_list_projects_shows_only_own_projects(client, auth_headers):
    client.post("/api/v1/projects", json={"name": "Project A"}, headers=auth_headers)
    client.post("/api/v1/projects", json={"name": "Project B"}, headers=auth_headers)

    response = client.get("/api/v1/projects", headers=auth_headers)

    assert response.status_code == 200
    names = {p["name"] for p in response.json()}
    assert names == {"Project A", "Project B"}
    assert all(p["role"] == "ADMIN" for p in response.json())


def test_get_project_forbidden_for_non_member(client, auth_headers):
    created = client.post(
        "/api/v1/projects", json={"name": "Owned"}, headers=auth_headers
    ).json()

    other_payload = {"email": "other@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=other_payload)
    other_login = client.post("/api/v1/auth/login", json=other_payload).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    response = client.get(f"/api/v1/projects/{created['id']}", headers=other_headers)

    assert response.status_code == 403


def test_archive_project_blocks_ingestion_but_not_reads(client, auth_headers):
    created = client.post(
        "/api/v1/projects", json={"name": "To Archive"}, headers=auth_headers
    ).json()
    api_key = created["api_key"]

    # Ingestion works while ACTIVE.
    trace_payload = {
        "traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 100.0}]
    }
    ok = client.post("/api/v1/traces", json=trace_payload, headers={"X-API-Key": api_key})
    assert ok.status_code == 201

    archived = client.post(f"/api/v1/projects/{created['id']}/archive", headers=auth_headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"

    # Ingestion is rejected once archived.
    blocked = client.post("/api/v1/traces", json=trace_payload, headers={"X-API-Key": api_key})
    assert blocked.status_code == 403

    # But existing data is still fully readable.
    listed = client.get(f"/api/v1/projects/{created['id']}/traces", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    get_resp = client.get(f"/api/v1/projects/{created['id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "ARCHIVED"


def test_archive_project_is_idempotent(client, auth_headers):
    created = client.post(
        "/api/v1/projects", json={"name": "Double Archive"}, headers=auth_headers
    ).json()

    first = client.post(f"/api/v1/projects/{created['id']}/archive", headers=auth_headers)
    second = client.post(f"/api/v1/projects/{created['id']}/archive", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "ARCHIVED"


def test_unarchive_project_restores_ingestion(client, auth_headers):
    created = client.post(
        "/api/v1/projects", json={"name": "Restore Me"}, headers=auth_headers
    ).json()
    api_key = created["api_key"]

    client.post(f"/api/v1/projects/{created['id']}/archive", headers=auth_headers)
    unarchived = client.post(f"/api/v1/projects/{created['id']}/unarchive", headers=auth_headers)
    assert unarchived.status_code == 200
    assert unarchived.json()["status"] == "ACTIVE"

    trace_payload = {
        "traces": [{"model": "gpt-4o", "provider": "openai", "prompt": "hi", "latency_ms": 100.0}]
    }
    ok = client.post("/api/v1/traces", json=trace_payload, headers={"X-API-Key": api_key})
    assert ok.status_code == 201


def test_archive_project_requires_admin(client, auth_headers):
    created = client.post(
        "/api/v1/projects", json={"name": "Not Yours To Archive"}, headers=auth_headers
    ).json()

    other_payload = {"email": "viewer@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=other_payload)
    other_login = client.post("/api/v1/auth/login", json=other_payload).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    client.post(
        f"/api/v1/projects/{created['id']}/members",
        json={"email": "viewer@example.com", "role": "VIEWER"},
        headers=auth_headers,
    )

    response = client.post(f"/api/v1/projects/{created['id']}/archive", headers=other_headers)

    assert response.status_code == 403


def test_archive_project_requires_membership(client, auth_headers):
    created = client.post(
        "/api/v1/projects", json={"name": "Someone Elses"}, headers=auth_headers
    ).json()

    other_payload = {"email": "outsider@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=other_payload)
    other_login = client.post("/api/v1/auth/login", json=other_payload).json()
    other_headers = {"Authorization": f"Bearer {other_login['access_token']}"}

    response = client.post(f"/api/v1/projects/{created['id']}/archive", headers=other_headers)

    assert response.status_code == 403
