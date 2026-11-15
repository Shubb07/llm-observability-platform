def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "supersecret123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "id" in body


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "supersecret123"}
    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 400


def test_register_duplicate_email_race_returns_400_not_500(client, db_session, monkeypatch):
    # Two requests for the same email can both pass the "does this email
    # already exist" check before either commits - simulate that by forcing
    # the check to miss a row that is already there, so the endpoint falls
    # through to the insert and has to rely on the unique constraint instead.
    from sqlalchemy.orm import Query

    from app.core.security import hash_password
    from app.models.user import User

    db_session.add(User(email="race@example.com", hashed_password=hash_password("whatever123")))
    db_session.commit()

    monkeypatch.setattr(Query, "first", lambda self: None)

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "race@example.com", "password": "supersecret123"},
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_returns_token(client):
    payload = {"email": "login@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 0


def test_login_wrong_password_rejected(client):
    payload = {"email": "wrongpw@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": "not-the-password"},
    )

    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers, registered_user):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == registered_user["email"]


def test_register_rejects_password_over_72_bytes(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "toolong@example.com", "password": "x" * 73},
    )
    assert response.status_code == 400


def test_login_sets_httponly_access_token_cookie(client):
    payload = {"email": "cookieuser@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", json=payload)

    assert "access_token" in response.cookies
    set_cookie_header = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie_header
    # Tests run with COOKIE_SECURE=false (see conftest.py), which maps to
    # samesite=lax - samesite=none requires Secure, which the test client
    # doesn't set, so a real browser would silently drop that cookie.
    assert "samesite=lax" in set_cookie_header


def test_me_authenticates_via_cookie_with_no_authorization_header(client):
    payload = {"email": "cookieauth@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)
    client.post("/api/v1/auth/login", json=payload)

    # TestClient's cookie jar resends the Set-Cookie from login automatically -
    # no Authorization header is attached here, same as a real browser
    # request that relies solely on the HttpOnly cookie.
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == payload["email"]


def test_logout_clears_cookie_and_revokes_cookie_based_session(client):
    payload = {"email": "logoutuser@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)
    client.post("/api/v1/auth/login", json=payload)

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 401


def test_logout_delete_cookie_matches_secure_attribute_in_production(client, monkeypatch):
    # Tests run with COOKIE_SECURE=false (samesite=lax), which never exercises
    # the samesite=none branch logout() shares with login()'s cookie-setting.
    # A SameSite=None cookie needs Secure too, or a real browser silently
    # drops the Set-Cookie outright - this asserts the header a real
    # (cookie_secure=true) deployment would send actually has it, which
    # login()'s cookie already does. Without secure=... on delete_cookie,
    # the deletion itself never reached the browser: "signing out" looked
    # like it worked (redirect to /login) but the original cookie stayed
    # valid, logging the same session straight back in on the next request.
    import app.api.auth as auth_module

    monkeypatch.setattr(auth_module.settings, "cookie_secure", True)

    response = client.post("/api/v1/auth/logout")

    set_cookie_header = response.headers["set-cookie"].lower()
    assert "secure" in set_cookie_header
    assert "samesite=none" in set_cookie_header


def test_bearer_header_still_works_without_cookie(client, auth_headers, registered_user):
    # Non-browser callers (curl, the SDK's own token management, /docs) never
    # get the cookie set in a browser's jar - the Authorization header path
    # from before this change must keep working on its own.
    client.cookies.clear()
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == registered_user["email"]
