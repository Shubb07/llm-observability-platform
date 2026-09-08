from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_project_membership
from app.core.db import get_db
from app.models.project import Project, ProjectMembership, ProjectRole
from app.models.user import User
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
