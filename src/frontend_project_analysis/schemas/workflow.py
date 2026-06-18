"""Workflow payload models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..core.domain import (
    ArtifactStatus,
    ArtifactType,
    DependencyType,
    ReviewerKind,
    ReviewKind,
    ReviewStatus,
)


class ArtifactInput(BaseModel):
    artifact_type: ArtifactType
    slug: str
    title: str
    source_path: str | None = None
    status: ArtifactStatus = ArtifactStatus.DRAFT
    metadata: dict[str, Any] = Field(default_factory=dict)


class DependencyInput(BaseModel):
    from_ref: str
    to_ref: str
    dependency_type: DependencyType = DependencyType.REQUIRES
    is_hard: bool = True


class FindingPayload(BaseModel):
    severity: str
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SemanticReviewPayload(BaseModel):
    decision: ReviewStatus
    summary: str
    reviewer_ref: str = "llm"
    model: str | None = None
    findings: list[FindingPayload] = Field(default_factory=list)


class ReviewRecord(BaseModel):
    artifact_ref: str
    review_kind: ReviewKind
    review_status: ReviewStatus
    reviewer_kind: ReviewerKind
    summary: str
    reviewer_ref: str = "system"
    payload: dict[str, Any] = Field(default_factory=dict)
    findings: list[FindingPayload] = Field(default_factory=list)


class ImportPreview(BaseModel):
    apply: bool = False
    files: list[Path] = Field(default_factory=list)
