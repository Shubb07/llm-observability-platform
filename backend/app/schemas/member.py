from pydantic import BaseModel, EmailStr

from app.models.project import ProjectRole


class MemberAdd(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.MEMBER


class MemberRoleUpdate(BaseModel):
    role: ProjectRole


class MemberOut(BaseModel):
    user_id: str
    email: str
    role: str

    model_config = {"from_attributes": True}
