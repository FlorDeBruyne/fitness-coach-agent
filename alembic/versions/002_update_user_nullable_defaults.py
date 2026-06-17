"""update_user_nullable_defaults

Revision ID: 899b9a8f998a
Revises: 5b3cb6133a16
Create Date: 2026-06-17 13:09:57.685889

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '899b9a8f998a'
down_revision: Union[str, Sequence[str], None] = '5b3cb6133a16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'height_cm', existing_type=sa.Float(), nullable=True)
    op.alter_column('users', 'weight_kg', existing_type=sa.Float(), nullable=True)
    op.drop_column('users', 'preferred_message_time_evening')
    op.drop_column('users', 'preferred_message_time_morning')


def downgrade() -> None:
    op.alter_column('users', 'height_cm', existing_type=sa.Float(), nullable=False)
    op.alter_column('users', 'weight_kg', existing_type=sa.Float(), nullable=False)
    op.add_column('users', sa.Column('preferred_message_time_morning',
                                      postgresql.TIME(),
                                      server_default=sa.text("'08:00:00'::time without time zone"),
                                      nullable=True))
    op.add_column('users', sa.Column('preferred_message_time_evening',
                                      postgresql.TIME(),
                                      server_default=sa.text("'20:00:00'::time without time zone"),
                                      nullable=True))
