"""add context to traces

Revision ID: 184c6facd18b
Revises: c3d4e5f6a1b2
Create Date: 2026-11-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '184c6facd18b'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('traces', sa.Column('context', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('traces', 'context')
