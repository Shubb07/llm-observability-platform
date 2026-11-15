"""unique membership per project and user

Revision ID: a1b2c3d4e5f6
Revises: 4dc2a535e0df
Create Date: 2026-11-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4dc2a535e0df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        'uq_membership_project_user', 'project_memberships', ['project_id', 'user_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_membership_project_user', 'project_memberships', type_='unique')
