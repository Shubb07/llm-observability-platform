from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_db
from app.core.rate_limit import rate_limit_auth
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _set_access_token_cookie(response: Response, token: str) -> None:
    # HttpOnly so the dashboard's own JS can never read this value (that's
    # the whole point of the cookie over the old localStorage/JS-cookie
    # approach - an XSS payload that can read localStorage can equally read
    # a non-HttpOnly cookie). The dashboard never sets or parses this cookie
    # itself; the browser attaches it automatically on same-origin requests,
    # and deps.py reads it as a fallback when there's no Authorization header.
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=settings.jwt_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        # The dashboard and backend are deployed on different onrender.com
        # subdomains, so this is a cross-site request as far as the browser
        # is concerned - "strict" (or "lax") never sends the cookie there,
        # which silently 401s every request. "None" requires Secure, which
        # is exactly cookie_secure's existing true-in-prod/false-for-local-
        # http split, so tie samesite to it instead of adding a new setting.
        samesite="none" if settings.cookie_secure else "lax",
        path="/",
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_auth)],
)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=payload.email).first()
    if existing is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    try:
        hashed = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    user = User(email=payload.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_auth)])
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")

    token = create_access_token(subject=user.id)
    # Set the browser's auth cookie here. The token is also returned in the
    # body below for non-browser callers (curl, the /docs UI, scripts) that
    # have no cookie jar and manage the bearer token themselves.
    _set_access_token_cookie(response, token)
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    # The dashboard can't delete this cookie itself (HttpOnly), so logging
    # out has to be a real request the backend answers with a clearing
    # Set-Cookie, not a client-side document.cookie write.
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        path="/",
        samesite="none" if settings.cookie_secure else "lax",
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
