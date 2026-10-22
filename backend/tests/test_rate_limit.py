from starlette.requests import Request

from app.core.rate_limit import MAX_ATTEMPTS, _client_ip, reset_for_tests


def make_request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


def test_client_ip_uses_rightmost_forwarded_entry():
    # Render's edge appends the connection's real address as the last hop -
    # that's the one entry in the chain that wasn't caller-supplied.
    request = make_request({"x-forwarded-for": "9.9.9.9, 10.0.0.5"})
    assert _client_ip(request) == "10.0.0.5"


def test_client_ip_is_not_fooled_by_a_spoofed_leftmost_value():
    # Regression test: taking the leftmost entry let an attacker bypass the
    # rate limiter entirely by sending a different fake X-Forwarded-For on
    # every request - each one bucketed as a "new" client. The rightmost
    # entry, which the attacker doesn't control, should be identical here.
    spoofed_a = make_request({"x-forwarded-for": "1.1.1.1, 203.0.113.9"})
    spoofed_b = make_request({"x-forwarded-for": "2.2.2.2, 203.0.113.9"})
    assert _client_ip(spoofed_a) == _client_ip(spoofed_b) == "203.0.113.9"


def test_login_rate_limit_blocks_after_max_attempts(client):
    reset_for_tests()
    headers = {"X-Forwarded-For": "198.51.100.1, 203.0.113.50"}
    payload = {"email": "nobody@example.com", "password": "wrong-password"}

    for _ in range(MAX_ATTEMPTS):
        response = client.post("/api/v1/auth/login", json=payload, headers=headers)
        assert response.status_code == 401  # wrong credentials, not yet rate-limited

    blocked = client.post("/api/v1/auth/login", json=payload, headers=headers)
    assert blocked.status_code == 429


def test_login_rate_limit_is_per_client_not_global(client):
    reset_for_tests()
    payload = {"email": "nobody@example.com", "password": "wrong-password"}
    attacker_headers = {"X-Forwarded-For": "198.51.100.1, 203.0.113.50"}
    other_user_headers = {"X-Forwarded-For": "198.51.100.2, 203.0.113.99"}

    for _ in range(MAX_ATTEMPTS):
        client.post("/api/v1/auth/login", json=payload, headers=attacker_headers)
    exhausted = client.post("/api/v1/auth/login", json=payload, headers=attacker_headers)
    assert exhausted.status_code == 429

    unaffected = client.post("/api/v1/auth/login", json=payload, headers=other_user_headers)
    assert unaffected.status_code == 401  # a different real client, not blocked
