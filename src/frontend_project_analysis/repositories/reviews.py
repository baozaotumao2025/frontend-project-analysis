"""Review and provider-audit repository helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..infrastructure.logging_utils import get_logger
from ..models import Artifact, ArtifactReview, ArtifactReviewFinding, ProviderCallAudit
from .dependencies import artifact_ref

logger = get_logger(__name__)


def record_review(
    session: Session,
    artifact: Artifact,
    review_kind,
    review_status,
    reviewer_kind,
    summary: str,
    reviewer_ref: str,
    payload: dict,
    findings: list[dict],
) -> ArtifactReview:
    review = ArtifactReview(
        artifact_id=artifact.id,
        version_id=artifact.current_version_id,
        review_kind=review_kind,
        review_status=review_status,
        reviewer_kind=reviewer_kind,
        summary=summary,
        reviewer_ref=reviewer_ref,
        payload_json=payload,
    )
    session.add(review)
    session.flush()
    for finding in findings:
        details = dict(finding.get("details", {}))
        if finding.get("evidence"):
            details["evidence"] = finding["evidence"]
        review.findings.append(
            ArtifactReviewFinding(
                severity=finding["severity"],
                code=finding["code"],
                message=finding["message"],
                details_json=details,
            )
        )
    logger.info(
        "Recorded %s review for %s with status %s",
        review_kind.value,
        artifact_ref(artifact),
        review_status.value,
    )
    return review


def record_provider_call_audit(
    session: Session,
    artifact: Artifact,
    trace_id: str,
    request_id: str,
    provider_name: str,
    error_code: str | None,
    model_name: str | None,
    endpoint: str,
    call_status: str,
    attempt_count: int,
    duration_ms: int,
    request_path: str | None,
    response_path: str | None,
    request_summary_json: dict,
    response_summary_json: dict,
    events_json: list[dict],
    error_message: str | None,
    review: ArtifactReview | None = None,
) -> ProviderCallAudit:
    audit = ProviderCallAudit(
        artifact_id=artifact.id,
        review_id=review.id if review else None,
        provider_name=provider_name,
        trace_id=trace_id,
        request_id=request_id,
        error_code=error_code,
        model_name=model_name,
        endpoint=endpoint,
        call_status=call_status,
        attempt_count=attempt_count,
        duration_ms=duration_ms,
        request_path=request_path,
        response_path=response_path,
        request_summary_json=request_summary_json,
        response_summary_json=response_summary_json,
        events_json=events_json,
        error_message=error_message,
    )
    session.add(audit)
    session.flush()
    logger.info(
        "Recorded provider call audit for %s via %s (%s)",
        artifact_ref(artifact),
        provider_name,
        call_status,
    )
    return audit
