"""Simple in-memory rate limiting for the unauthenticated auth endpoints.

Login and register have no other defense against credential stuffing or
brute-force password guessing - bcrypt slows down a single guess, but says
nothing about guess *rate*. A fixed window per client IP is enough for a
single-instance deployment (this project's free-tier Render service) without
pulling in Redis or an extra dependency; it resets on restart and doesn't
share state across instances, which is an explicit tradeoff for simplicity
at this scale, not an oversight.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

WINDOW_SECONDS = 60
MAX_ATTEMPTS = 10

_attempts: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    # Render (and most PaaS) terminate TLS at a proxy in front of the app,
    # so request.client.host would be the proxy's address, not the caller's.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_auth(request: Request) -> None:
    client_ip = _client_ip(request)
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS

    timestamps = _attempts[client_ip]
    while timestamps and timestamps[0] < cutoff:
        timestamps.pop(0)

    if len(timestamps) >= MAX_ATTEMPTS:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many attempts - try again in a minute",
        )
    timestamps.append(now)


def reset_for_tests() -> None:
    """Called from conftest.py between tests so attempt counts don't leak
    across test functions that all share this process's module state."""
    _attempts.clear()
