from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.project import Project, ProjectMembership
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")

    return user


def get_project_membership(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectMembership:
    membership = (
        db.query(ProjectMembership)
        .filter_by(project_id=project_id, user_id=current_user.id)
        .first()
    )
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this project")
    return membership


def require_admin(
    membership: ProjectMembership = Depends(get_project_membership),
) -> ProjectMembership:
    if membership.role != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required for this action")
    return membership


def get_project_by_api_key(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Project:
    if x_api_key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")

    project = db.query(Project).filter_by(api_key=x_api_key).first()
    if project is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    if project.status != "ACTIVE":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Project is not active")

    return project


def get_project_by_membership_or_api_key(
    project_id: str,
    x_api_key: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Project:
    """Read access to one project's data, proven either way: a project API
    key (what the MCP server and other external clients use - already scoped
    to one project, same key that ingest_traces accepts) or a JWT bearer
    token plus membership (what the dashboard uses). Kept separate from
    get_project_by_api_key because that one is ingest-only and never checks
    project_id against the URL - here the key must match the project being
    asked about, not just any active project."""
    if x_api_key is not None:
        project = db.query(Project).filter_by(api_key=x_api_key).first()
        if project is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
        if project.id != project_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "API key does not grant access to this project")
        if project.status != "ACTIVE":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Project is not active")
        return project

    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key or bearer token")

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")

    membership = db.query(ProjectMembership).filter_by(project_id=project_id, user_id=user.id).first()
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this project")
    return membership.project
