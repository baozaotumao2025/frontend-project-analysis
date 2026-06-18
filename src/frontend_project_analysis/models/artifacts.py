"""Artifact, dependency, transition, and provider audit models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.domain import ArtifactStatus, ArtifactType, DependencyType
from .base import Base

if TYPE_CHECKING:
    from .projects import Project
    from .reviews import ArtifactReview


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    project: Mapped[Project] = relationship("Project", back_populates="artifacts")
    current_version: Mapped[ArtifactVersion | None] = relationship(
        "ArtifactVersion",
        foreign_keys=[current_version_id],
    )
    versions: Mapped[list[ArtifactVersion]] = relationship(
        "ArtifactVersion",
        back_populates="artifact",
        foreign_keys="ArtifactVersion.artifact_id",
        cascade="all, delete-orphan",
    )
    outgoing_dependencies: Mapped[list[ArtifactDependency]] = relationship(
        "ArtifactDependency",
        back_populates="from_artifact",
        foreign_keys="ArtifactDependency.from_artifact_id",
        cascade="all, delete-orphan",
    )
    incoming_dependencies: Mapped[list[ArtifactDependency]] = relationship(
        "ArtifactDependency",
        back_populates="to_artifact",
        foreign_keys="ArtifactDependency.to_artifact_id",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list[ArtifactReview]] = relationship(
        "ArtifactReview",
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
    provider_call_audits: Mapped[list[ProviderCallAudit]] = relationship(
        "ProviderCallAudit",
        back_populates="artifact",
        cascade="all, delete-orphan",
    )
    transitions: Mapped[list[ArtifactTransition]] = relationship(
        "ArtifactTransition",
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    artifact: Mapped[Artifact] = relationship(
        "Artifact",
        back_populates="versions",
        foreign_keys=[artifact_id],
    )


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    from_artifact: Mapped[Artifact] = relationship(
        "Artifact",
        back_populates="outgoing_dependencies",
        foreign_keys=[from_artifact_id],
    )
    to_artifact: Mapped[Artifact] = relationship(
        "Artifact",
        back_populates="incoming_dependencies",
        foreign_keys=[to_artifact_id],
    )


class ArtifactTransition(Base):
    __tablename__ = "artifact_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"))
    from_status: Mapped[str] = mapped_column(String(64))
    to_status: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(String(255), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    artifact: Mapped[Artifact] = relationship(
        "Artifact",
        back_populates="transitions",
    )


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    artifact: Mapped[Artifact] = relationship(
        "Artifact",
        back_populates="provider_call_audits",
    )
    review: Mapped[ArtifactReview | None] = relationship(
        "ArtifactReview",
        back_populates="provider_call_audits",
        foreign_keys=[review_id],
    )
