"""Add provider error code tracking.

Revision ID: 0003_provider_error_codes
Revises: 0002_provider_audit_events
Create Date: 2026-06-18 00:00:00.000002
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_provider_error_codes"
down_revision = "0002_provider_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "provider_call_audits",
        sa.Column("error_code", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    with op.batch_alter_table("provider_call_audits") as batch_op:
        batch_op.drop_column("error_code")
