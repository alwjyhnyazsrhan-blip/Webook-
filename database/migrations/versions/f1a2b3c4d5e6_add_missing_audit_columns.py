"""add missing audit columns: success_rate, last_error, max_price, sniper_mode

Revision ID: f1a2b3c4d5e6
Revises: e1b2c3d4e5f6
Create Date: 2025-01-01 00:00:00.000000

Forensic audit confirmed these columns exist in SQLAlchemy models
but were absent from the live schema, causing AttributeError crashes
at runtime when the ORM tried to read/write them.
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ auth_sessions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Add success_rate (0-100 score) if missing
    op.execute("""
        ALTER TABLE auth_sessions
        ADD COLUMN IF NOT EXISTS success_rate INTEGER DEFAULT 100;
    """)

    # Add last_error string if missing
    op.execute("""
        ALTER TABLE auth_sessions
        ADD COLUMN IF NOT EXISTS last_error VARCHAR DEFAULT NULL;
    """)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ live_events â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # max_price was dropped in e1b2c3d4e5f6 downgrade path but model still has it
    op.execute("""
        ALTER TABLE live_events
        ADD COLUMN IF NOT EXISTS max_price INTEGER DEFAULT NULL;
    """)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ reservation_tasks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # sniper_mode: skip human simulation for maximum sniping speed
    op.execute("""
        ALTER TABLE reservation_tasks
        ADD COLUMN IF NOT EXISTS sniper_mode BOOLEAN DEFAULT FALSE;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE auth_sessions DROP COLUMN IF EXISTS success_rate;")
    op.execute("ALTER TABLE auth_sessions DROP COLUMN IF EXISTS last_error;")
    op.execute("ALTER TABLE live_events DROP COLUMN IF EXISTS max_price;")
    op.execute("ALTER TABLE reservation_tasks DROP COLUMN IF EXISTS sniper_mode;")

