from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_project_membership, require_admin
from app.core.db import get_db
from app.models.project import Project, ProjectMembership, ProjectRole
from app.models.user import User
from app.schemas.member import MemberAdd, MemberOut, MemberRoleUpdate
from app.schemas.project import ProjectCreate, ProjectOut, ProjectSummary

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(name=payload.name)
    db.add(project)
    db.flush()

    membership = ProjectMembership(
        project_id=project.id,
        user_id=current_user.id,
        role=ProjectRole.ADMIN.value,
    )
    db.add(membership)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectSummary])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = db.query(ProjectMembership).filter_by(user_id=current_user.id).all()
    return [
        ProjectSummary(
            id=m.project.id,
            name=m.project.name,
            status=m.project.status,
            role=m.role,
            created_at=m.project.created_at,
        )
        for m in memberships
    ]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(membership: ProjectMembership = Depends(get_project_membership)):
    return membership.project


@router.get("/{project_id}/members", response_model=list[MemberOut])
def list_members(
    membership: ProjectMembership = Depends(get_project_membership),
    db: Session = Depends(get_db),
):
    memberships = db.query(ProjectMembership).filter_by(project_id=membership.project_id).all()
    return [MemberOut(user_id=m.user_id, email=m.user.email, role=m.role) for m in memberships]


@router.post("/{project_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: str,
    payload: MemberAdd,
    _: ProjectMembership = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=payload.email).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user is registered with that email")

    existing = db.query(ProjectMembership).filter_by(project_id=project_id, user_id=user.id).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "User is already a member of this project")

    membership = ProjectMembership(project_id=project_id, user_id=user.id, role=payload.role.value)
    db.add(membership)
    db.commit()
    return MemberOut(user_id=user.id, email=user.email, role=membership.role)


@router.patch("/{project_id}/members/{user_id}", response_model=MemberOut)
def update_member_role(
    project_id: str,
    user_id: str,
    payload: MemberRoleUpdate,
    _: ProjectMembership = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(ProjectMembership).filter_by(project_id=project_id, user_id=user_id).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That user is not a member of this project")

    if target.role == ProjectRole.ADMIN.value and payload.role != ProjectRole.ADMIN:
        _ensure_not_last_admin(db, project_id)

    target.role = payload.role.value
    db.commit()
    return MemberOut(user_id=target.user_id, email=target.user.email, role=target.role)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    project_id: str,
    user_id: str,
    _: ProjectMembership = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(ProjectMembership).filter_by(project_id=project_id, user_id=user_id).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That user is not a member of this project")

    if target.role == ProjectRole.ADMIN.value:
        _ensure_not_last_admin(db, project_id)

    db.delete(target)
    db.commit()


def _ensure_not_last_admin(db: Session, project_id: str) -> None:
    admin_count = (
        db.query(ProjectMembership)
        .filter_by(project_id=project_id, role=ProjectRole.ADMIN.value)
        .count()
    )
    if admin_count <= 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Cannot remove or demote the project's last Admin",
        )
