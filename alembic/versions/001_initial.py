"""initial



Revision ID: 5b3cb6133a16
Revises: 
Create Date: 2026-06-11 21:39:40.199850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b3cb6133a16'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            firstname VARCHAR(100),
            lastname VARCHAR(100),
            gender VARCHAR(20),
            age INTEGER,
            height_cm FLOAT,
            weight_kg FLOAT,
            fitness_level VARCHAR(50),
            telegram_chat_id BIGINT UNIQUE NOT NULL,
            preferred_language VARCHAR(10) DEFAULT 'nl',
            timezone VARCHAR(50) DEFAULT 'Europe/Brussels',
            preferred_message_time_morning TIME DEFAULT '08:00',
            preferred_message_time_evening TIME DEFAULT '20:00',
            onboarding_completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS goals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                type VARCHAR(100) NOT NULL,
                description TEXT,
                target_value FLOAT,
                current_value FLOAT DEFAULT 0,
                unit VARCHAR(50),
                status VARCHAR(20) DEFAULT 'active',
                deadline DATE,
                notes TEXT,
                completed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
   """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS injuries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            affected_area VARCHAR(100),
            severity VARCHAR(20),
            is_active BOOLEAN DEFAULT TRUE,
            notes TEXT,
            started_at DATE,
            resolved_at DATE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        
            CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
        
            CREATE TRIGGER goals_updated_at BEFORE UPDATE ON goals
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
        
            CREATE TRIGGER injuries_updated_at BEFORE UPDATE ON injuries
                FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('injuries')
    op.drop_table('goals')
    op.drop_table('users')
