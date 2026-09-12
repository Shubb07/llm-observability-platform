import pytest


@pytest.fixture()
def project(client, auth_headers):
    response = client.post("/api/v1/projects", json={"name": "Membership Project"}, headers=auth_headers)
    return response.json()


@pytest.fixture()
def other_user(client):
    payload = {"email": "member2@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)
    login = client.post("/api/v1/auth/login", json=payload).json()
    return {"email": payload["email"], "headers": {"Authorization": f"Bearer {login['access_token']}"}}


def test_creator_is_listed_as_admin(client, auth_headers, project, registered_user):
    response = client.get(f"/api/v1/projects/{project['id']}/members", headers=auth_headers)

    assert response.status_code == 200
    members = response.json()
    assert len(members) == 1
    assert members[0]["email"] == registered_user["email"]
    assert members[0]["role"] == "ADMIN"


def test_admin_can_add_member(client, auth_headers, project, other_user):
    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": other_user["email"], "role": "VIEWER"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["role"] == "VIEWER"

    listed = client.get(f"/api/v1/projects/{project['id']}/members", headers=auth_headers).json()
    assert len(listed) == 2


def test_non_admin_cannot_add_member(client, auth_headers, project, other_user):
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": other_user["email"], "role": "VIEWER"},
        headers=auth_headers,
    )

    third_payload = {"email": "member3@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=third_payload)
    third_login = client.post("/api/v1/auth/login", json=third_payload).json()
    third_headers = {"Authorization": f"Bearer {third_login['access_token']}"}

    # other_user is only a VIEWER on this project - can't add members.
    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": third_payload["email"], "role": "VIEWER"},
        headers=other_user["headers"],
    )
    assert response.status_code == 403


def test_add_member_requires_existing_user(client, auth_headers, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "nobody@example.com", "role": "MEMBER"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_add_member_rejects_duplicate(client, auth_headers, project, other_user):
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": other_user["email"], "role": "MEMBER"},
        headers=auth_headers,
    )
    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": other_user["email"], "role": "MEMBER"},
        headers=auth_headers,
    )
    assert response.status_code == 409


def test_admin_can_change_member_role(client, auth_headers, project, other_user):
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": other_user["email"], "role": "VIEWER"},
        headers=auth_headers,
    )
    members = client.get(f"/api/v1/projects/{project['id']}/members", headers=auth_headers).json()
    other_user_id = next(m["user_id"] for m in members if m["email"] == other_user["email"])

    response = client.patch(
        f"/api/v1/projects/{project['id']}/members/{other_user_id}",
        json={"role": "MEMBER"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["role"] == "MEMBER"


def test_cannot_demote_last_admin(client, auth_headers, project, registered_user):
    members = client.get(f"/api/v1/projects/{project['id']}/members", headers=auth_headers).json()
    admin_id = members[0]["user_id"]

    response = client.patch(
        f"/api/v1/projects/{project['id']}/members/{admin_id}",
        json={"role": "MEMBER"},
        headers=auth_headers,
    )
    assert response.status_code == 409


def test_admin_can_remove_member(client, auth_headers, project, other_user):
    client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": other_user["email"], "role": "VIEWER"},
        headers=auth_headers,
    )
    members = client.get(f"/api/v1/projects/{project['id']}/members", headers=auth_headers).json()
    other_user_id = next(m["user_id"] for m in members if m["email"] == other_user["email"])

    response = client.delete(
        f"/api/v1/projects/{project['id']}/members/{other_user_id}", headers=auth_headers
    )
    assert response.status_code == 204

    remaining = client.get(f"/api/v1/projects/{project['id']}/members", headers=auth_headers).json()
    assert len(remaining) == 1


def test_cannot_remove_last_admin(client, auth_headers, project, registered_user):
    members = client.get(f"/api/v1/projects/{project['id']}/members", headers=auth_headers).json()
    admin_id = members[0]["user_id"]

    response = client.delete(f"/api/v1/projects/{project['id']}/members/{admin_id}", headers=auth_headers)
    assert response.status_code == 409
