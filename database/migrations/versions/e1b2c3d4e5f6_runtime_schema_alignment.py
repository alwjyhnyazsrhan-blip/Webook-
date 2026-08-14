"""runtime_schema_alignment

Revision ID: e1b2c3d4e5f6
Revises: d40c8b30be36
Create Date: 2026-05-07
"""
from typing import Seuence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1b2c3d4e5f6"
down_revision: Union[str, None] = "d40c8b30be36"
branch_labels: Union[str, Seuence[str], None] = None
depends_on: Union[str, Seuence[str], None] = None


def upgrade() -> None:
    op.add_column("live_events", sa.Column("hydration_status", sa.String(), nullable=True, server_default="DISCOVERED"))
    op.add_column("live_events", sa.Column("chart_token", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("image_url", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("venue_address", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("max_price", sa.Integer(), nullable=True))
    op.add_column("live_events", sa.Column("seats_provider", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("chart_key", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("event_key", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("workspace_key", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("interactive_map_url", sa.String(), nullable=True))
    op.add_column("live_events", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("live_events", sa.Column("hydrated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("live_events", sa.Column("hydration_attempts", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("live_events", sa.Column("last_hydration_error", sa.String(), nullable=True))

    op.add_column("auth_sessions", sa.Column("success_rate", sa.Integer(), nullable=True, server_default="100"))
    op.add_column("auth_sessions", sa.Column("last_error", sa.String(), nullable=True))

    op.add_column("user_global_prefs", sa.Column("language", sa.String(), nullable=True, server_default="ar"))
    op.alter_column("user_global_prefs", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column("user_event_subscriptions", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger())
    op.alter_column("reservation_tasks", "user_id", existing_type=sa.Integer(), type_=sa.BigInteger())


def downgrade() -> None:
    op.drop_column("auth_sessions", "last_error")
    op.drop_column("auth_sessions", "success_rate")

    op.alter_column("reservation_tasks", "user_id", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column("user_event_subscriptions", "user_id", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.alter_column("user_global_prefs", "user_id", existing_type=sa.BigInteger(), type_=sa.Integer())
    op.drop_column("user_global_prefs", "language")

    op.drop_column("live_events", "last_hydration_error")
    op.drop_column("live_events", "hydration_attempts")
    op.drop_column("live_events", "hydrated_at")
    op.drop_column("live_events", "last_verified_at")
    op.drop_column("live_events", "interactive_map_url")
    op.drop_column("live_events", "workspace_key")
    op.drop_column("live_events", "event_key")
    op.drop_column("live_events", "chart_key")
    op.drop_column("live_events", "seats_provider")
    op.drop_column("live_events", "venue_address")
    op.drop_column("live_events", "image_url")
    op.drop_column("live_events", "max_price")
    op.drop_column("live_events", "chart_token")
    op.drop_column("live_events", "hydration_status")

