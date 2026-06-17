"""Add provider audit event timeline.

Revision ID: 0002_provider_audit_events
Revises: 0001_initial_schema
Create Date: 2026-06-18 00:00:00.000001
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_provider_audit_events"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "provider_call_audits",
        sa.Column("events_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    with op.batch_alter_table("provider_call_audits") as batch_op:
        batch_op.drop_column("events_json")
