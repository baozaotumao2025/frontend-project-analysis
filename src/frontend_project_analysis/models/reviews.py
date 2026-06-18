"""Review record and finding models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.domain import ReviewerKind, ReviewKind, ReviewStatus
from .base import Base

if TYPE_CHECKING:
    from .artifacts import Artifact, ProviderCallAudit


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    artifact: Mapped[Artifact] = relationship(
        "Artifact",
        back_populates="reviews",
    )
    findings: Mapped[list[ArtifactReviewFinding]] = relationship(
        "ArtifactReviewFinding",
        back_populates="review",
        cascade="all, delete-orphan",
    )
    provider_call_audits: Mapped[list[ProviderCallAudit]] = relationship(
        "ProviderCallAudit",
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

    review: Mapped[ArtifactReview] = relationship(
        "ArtifactReview",
        back_populates="findings",
    )
