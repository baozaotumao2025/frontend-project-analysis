"""Initial workflow schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-18 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


artifact_type = sa.Enum(
    "PERSONA",
    "STORY_MAP",
    "PAGE",
    "FEATURE",
    "GWT",
    "FEATURE_SPEC",
    name="artifacttype",
)
artifact_status = sa.Enum(
    "DRAFT",
    "STRUCTURALLY_VALID",
    "SEMANTIC_REVIEW",
    "APPROVED",
    "REJECTED",
    "STALE",
    "SUPERSEDED",
    "ARCHIVED",
    name="artifactstatus",
)
dependency_type = sa.Enum(
    "REQUIRES",
    "DERIVED_FROM",
    "COVERS",
    "SERVES",
    "IMPLEMENTS",
    "SUPERCEDES",
    name="dependencytype",
)
review_kind = sa.Enum("STRUCTURAL", "SEMANTIC", name="reviewkind")
review_status = sa.Enum("PASSED", "FAILED", "NEEDS_REVISION", name="reviewstatus")
reviewer_kind = sa.Enum("RULE_ENGINE", "LLM", "HUMAN", name="reviewerkind")


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("root_path", sa.String(length=1024), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("key", name="uq_projects_key"),
    )
    op.create_index("ix_projects_key", "projects", ["key"], unique=True)

    op.create_table(
        "artifact_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.Integer(),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("body_snapshot", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("artifact_id", "version_no", name="uq_artifact_version_no"),
    )

    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("artifact_type", artifact_type, nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("status", artifact_status, nullable=False),
        sa.Column("source_path", sa.String(length=1024), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column(
            "current_version_id",
            sa.Integer(),
            sa.ForeignKey("artifact_versions.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "artifact_type", "slug", name="uq_artifact_identity"),
    )

    op.create_table(
        "artifact_dependencies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "from_artifact_id",
            sa.Integer(),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_artifact_id",
            sa.Integer(),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dependency_type", dependency_type, nullable=False),
        sa.Column("is_hard", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "from_artifact_id",
            "to_artifact_id",
            "dependency_type",
            name="uq_artifact_dependency",
        ),
    )

    op.create_table(
        "artifact_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.Integer(),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "version_id",
            sa.Integer(),
            sa.ForeignKey("artifact_versions.id"),
            nullable=True,
        ),
        sa.Column("review_kind", review_kind, nullable=False),
        sa.Column("review_status", review_status, nullable=False),
        sa.Column("reviewer_kind", reviewer_kind, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("reviewer_ref", sa.String(length=255), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "artifact_review_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "review_id",
            sa.Integer(),
            sa.ForeignKey("artifact_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
    )

    op.create_table(
        "artifact_transitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.Integer(),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(length=64), nullable=False),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "provider_call_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "artifact_id",
            sa.Integer(),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "review_id",
            sa.Integer(),
            sa.ForeignKey("artifact_reviews.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("endpoint", sa.String(length=1024), nullable=False),
        sa.Column("call_status", sa.String(length=64), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("request_path", sa.String(length=1024), nullable=True),
        sa.Column("response_path", sa.String(length=1024), nullable=True),
        sa.Column("request_summary_json", sa.JSON(), nullable=False),
        sa.Column("response_summary_json", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_provider_call_audits_trace_id", "provider_call_audits", ["trace_id"])
    op.create_index("ix_provider_call_audits_request_id", "provider_call_audits", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_provider_call_audits_request_id", table_name="provider_call_audits")
    op.drop_index("ix_provider_call_audits_trace_id", table_name="provider_call_audits")
    op.drop_table("provider_call_audits")
    op.drop_table("artifact_transitions")
    op.drop_table("artifact_review_findings")
    op.drop_table("artifact_reviews")
    op.drop_table("artifact_dependencies")
    op.drop_table("artifacts")
    op.drop_table("artifact_versions")
    op.drop_index("ix_projects_key", table_name="projects")
    op.drop_table("projects")
