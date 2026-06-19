"""Manifest export helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ...models import Artifact, ArtifactDependency, ArtifactReview, Project
from ...repositories.dependencies import artifact_ref


def export_manifest(session: Session, project: Project) -> dict:
    artifacts = list(
        session.scalars(
            select(Artifact)
            .where(Artifact.project_id == project.id)
            .options(
                selectinload(Artifact.outgoing_dependencies).selectinload(
                    ArtifactDependency.to_artifact
                ),
                selectinload(Artifact.reviews).selectinload(ArtifactReview.findings),
                selectinload(Artifact.provider_call_audits),
            )
        )
    )
    return {
        "project": {"key": project.key, "name": project.name, "root_path": project.root_path},
        "artifacts": [
            {
                "ref": artifact_ref(item),
                "title": item.title,
                "round": item.round,
                "status": item.status.value,
                "source_path": item.source_path,
                "metadata": item.metadata_json,
                "dependencies": [
                    {
                        "to": artifact_ref(dep.to_artifact),
                        "type": dep.dependency_type.value,
                        "is_hard": dep.is_hard,
                    }
                    for dep in item.outgoing_dependencies
                ],
                "reviews": [
                    {
                        "kind": review.review_kind.value,
                        "status": review.review_status.value,
                        "reviewer_kind": review.reviewer_kind.value,
                        "summary": review.summary,
                        "reviewer_ref": review.reviewer_ref,
                        "findings": [
                            {
                                "severity": finding.severity,
                                "code": finding.code,
                                "message": finding.message,
                                "details": finding.details_json,
                            }
                            for finding in review.findings
                        ],
                    }
                    for review in item.reviews
                ],
                "provider_call_audits": [
                    {
                        "provider_name": audit.provider_name,
                        "trace_id": audit.trace_id,
                        "request_id": audit.request_id,
                        "error_code": audit.error_code,
                        "model_name": audit.model_name,
                        "endpoint": audit.endpoint,
                        "call_status": audit.call_status,
                        "attempt_count": audit.attempt_count,
                        "duration_ms": audit.duration_ms,
                        "request_path": audit.request_path,
                        "response_path": audit.response_path,
                        "events": audit.events_json,
                        "error_message": audit.error_message,
                    }
                    for audit in item.provider_call_audits
                ],
            }
            for item in artifacts
        ],
    }
