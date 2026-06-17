"""Pydantic payload models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .domain import (
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


class OpenAIReviewRequest(BaseModel):
    model: str
    input: list[dict[str, Any]]
    text: dict[str, Any]
    max_output_tokens: int


class OpenAIReviewResponse(BaseModel):
    output: list[dict[str, Any]]


class AnthropicReviewRequest(BaseModel):
    model: str
    max_tokens: int
    system: str
    messages: list[dict[str, Any]]


class AnthropicReviewResponse(BaseModel):
    content: list[dict[str, Any]]


class GeminiReviewRequest(BaseModel):
    system_instruction: dict[str, Any]
    contents: list[dict[str, Any]]
    generationConfig: dict[str, Any]


class GeminiReviewResponse(BaseModel):
    candidates: list[dict[str, Any]]


class ProviderAttemptPayload(BaseModel):
    attempt_no: int
    status: str
    duration_ms: int
    error: str | None = None
    http_status: int | None = None
    request_id: str | None = None


class ProviderAuditEventPayload(BaseModel):
    event_type: str
    message: str
    offset_ms: int = 0
    attempt_no: int | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ProviderAuditPayload(BaseModel):
    trace_id: str
    request_id: str
    provider_name: str
    error_code: str | None = None
    model_name: str | None = None
    endpoint: str
    call_status: str
    attempt_count: int
    duration_ms: int
    request_json: dict[str, Any]
    response_json: dict[str, Any] | None = None
    error_message: str | None = None
    attempts: list[ProviderAttemptPayload] = Field(default_factory=list)
    events: list[ProviderAuditEventPayload] = Field(default_factory=list)


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
