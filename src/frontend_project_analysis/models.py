"""SQLAlchemy models for workflow state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .domain import (
    ArtifactStatus,
    ArtifactType,
    DependencyType,
    ReviewerKind,
    ReviewKind,
    ReviewStatus,
)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    root_path: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    artifacts: Mapped[list[Artifact]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("project_id", "artifact_type", "slug", name="uq_artifact_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType))
    slug: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    round: Mapped[int] = mapped_column(Integer)
    status: Mapped[ArtifactStatus] = mapped_column(
        Enum(ArtifactStatus),
        default=ArtifactStatus.DRAFT,
    )
    source_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("artifact_versions.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    project: Mapped[Project] = relationship(back_populates="artifacts")
    current_version: Mapped[ArtifactVersion | None] = relationship(
        foreign_keys=[current_version_id]
    )
    versions: Mapped[list[ArtifactVersion]] = relationship(
        back_populates="artifact",
        foreign_keys="ArtifactVersion.artifact_id",
        cascade="all, delete-orphan",
    )
    outgoing_dependencies: Mapped[list[ArtifactDependency]] = relationship(
        back_populates="from_artifact",
        foreign_keys="ArtifactDependency.from_artifact_id",
        cascade="all, delete-orphan",
    )
    incoming_dependencies: Mapped[list[ArtifactDependency]] = relationship(
        back_populates="to_artifact",
        foreign_keys="ArtifactDependency.to_artifact_id",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list[ArtifactReview]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
    provider_call_audits: Mapped[list[ProviderCallAudit]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
    transitions: Mapped[list[ArtifactTransition]] = relationship(
        back_populates="artifact",
        cascade="all, delete-orphan",
    )


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"
    __table_args__ = (UniqueConstraint("artifact_id", "version_no", name="uq_artifact_version_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"))
    version_no: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    body_snapshot: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(255), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    artifact: Mapped[Artifact] = relationship(back_populates="versions", foreign_keys=[artifact_id])


class ArtifactDependency(Base):
    __tablename__ = "artifact_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "from_artifact_id",
            "to_artifact_id",
            "dependency_type",
            name="uq_artifact_dependency",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"))
    to_artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"))
    dependency_type: Mapped[DependencyType] = mapped_column(Enum(DependencyType))
    is_hard: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    from_artifact: Mapped[Artifact] = relationship(
        back_populates="outgoing_dependencies",
        foreign_keys=[from_artifact_id],
    )
    to_artifact: Mapped[Artifact] = relationship(
        back_populates="incoming_dependencies",
        foreign_keys=[to_artifact_id],
    )


class ArtifactReview(Base):
    __tablename__ = "artifact_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"))
    version_id: Mapped[int | None] = mapped_column(
        ForeignKey("artifact_versions.id"),
        nullable=True,
    )
    review_kind: Mapped[ReviewKind] = mapped_column(Enum(ReviewKind))
    review_status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus))
    reviewer_kind: Mapped[ReviewerKind] = mapped_column(Enum(ReviewerKind))
    summary: Mapped[str] = mapped_column(Text)
    reviewer_ref: Mapped[str] = mapped_column(String(255), default="system")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    artifact: Mapped[Artifact] = relationship(back_populates="reviews")
    findings: Mapped[list[ArtifactReviewFinding]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
    provider_call_audits: Mapped[list[ProviderCallAudit]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )


class ArtifactReviewFinding(Base):
    __tablename__ = "artifact_review_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("artifact_reviews.id", ondelete="CASCADE"))
    severity: Mapped[str] = mapped_column(String(32))
    code: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)

    review: Mapped[ArtifactReview] = relationship(back_populates="findings")


class ArtifactTransition(Base):
    __tablename__ = "artifact_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"))
    from_status: Mapped[str] = mapped_column(String(64))
    to_status: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(String(255), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    artifact: Mapped[Artifact] = relationship(back_populates="transitions")


class ProviderCallAudit(Base):
    __tablename__ = "provider_call_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"))
    review_id: Mapped[int | None] = mapped_column(
        ForeignKey("artifact_reviews.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider_name: Mapped[str] = mapped_column(String(100))
    trace_id: Mapped[str] = mapped_column(String(64), index=True)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(1024))
    call_status: Mapped[str] = mapped_column(String(64))
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    request_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    response_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    request_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    response_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    events_json: Mapped[list] = mapped_column(JSON, default=list)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    artifact: Mapped[Artifact] = relationship(back_populates="provider_call_audits")
    review: Mapped[ArtifactReview | None] = relationship(
        back_populates="provider_call_audits",
        foreign_keys=[review_id],
    )
