"""add_injury_severity_constraint

Revision ID: b418de4a4a7d
Revises: 95347fc235b8
Create Date: 2026-08-02 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b418de4a4a7d'
down_revision: Union[str, Sequence[str], None] = '95347fc235b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        'ck_injuries_severity_allowed',
        'injuries',
        "severity IN ('licht', 'matig', 'ernstig')"
    )


def downgrade() -> None:
    op.drop_constraint('ck_injuries_severity_allowed', 'injuries', type_='check')
