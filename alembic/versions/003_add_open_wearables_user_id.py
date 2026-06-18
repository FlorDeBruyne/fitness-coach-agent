"""add_open_wearables_user_id

Revision ID: 2e5e7e7dc5ca
Revises: 899b9a8f998a
Create Date: 2026-06-18 23:32:35.991498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e5e7e7dc5ca'
down_revision: Union[str, Sequence[str], None] = '899b9a8f998a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('open_wearables_user_id', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'open_wearables_user_id')
