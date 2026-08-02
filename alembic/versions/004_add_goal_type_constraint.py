"""add_goal_type_constraint

Revision ID: 95347fc235b8
Revises: 2e5e7e7dc5ca
Create Date: 2026-08-02 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95347fc235b8'
down_revision: Union[str, Sequence[str], None] = '2e5e7e7dc5ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        'ck_goals_type_allowed',
        'goals',
        "type IN ('hardlopen', 'kracht', 'cardio', 'gewicht', 'flexibiliteit', 'herstel')"
    )


def downgrade() -> None:
    op.drop_constraint('ck_goals_type_allowed', 'goals', type_='check')
