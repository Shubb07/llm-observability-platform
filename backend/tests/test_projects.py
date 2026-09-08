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
