"""add_user_location

Revision ID: 489b45337e8d
Revises: b418de4a4a7d
Create Date: 2026-08-04 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '489b45337e8d'
down_revision: Union[str, Sequence[str], None] = 'b418de4a4a7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'longitude')
    op.drop_column('users', 'latitude')
