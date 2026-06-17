"""Export helpers for manifests, relations, and JSON payloads."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .domain import ArtifactType
from .models import Artifact, ArtifactDependency, ArtifactReview, Project
from .repositories import artifact_ref, list_artifacts


def export_json_to_path(payload: dict, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return destination


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


def render_relations_markdown(session: Session, project: Project, root: Path) -> list[Path]:
    artifacts = list_artifacts(session, project)
    persona_story_page_lines = [
        "# Persona Story Page Matrix",
        "",
        "| From | Dependency | To | Hard |",
        "| --- | --- | --- | --- |",
    ]
    feature_coverage_lines = [
        "# Feature Coverage Matrix",
        "",
        "| Feature | Dependency | Related Artifact | Hard |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in artifacts:
        ref = artifact_ref(artifact)
        for dependency in artifact.outgoing_dependencies:
            row = (
                f"| {ref} | {dependency.dependency_type.value} | "
                f"{artifact_ref(dependency.to_artifact)} | "
                f"{'yes' if dependency.is_hard else 'no'} |"
            )
            if artifact.artifact_type in {
                ArtifactType.PERSONA,
                ArtifactType.STORY_MAP,
                ArtifactType.PAGE,
            }:
                persona_story_page_lines.append(row)
            if artifact.artifact_type == ArtifactType.FEATURE:
                feature_coverage_lines.append(row)
    relations_dir = root / "docs" / "relations"
    relations_dir.mkdir(parents=True, exist_ok=True)
    psp_path = relations_dir / "persona-story-page-matrix.md"
    feature_path = relations_dir / "feature-coverage-matrix.md"
    psp_path.write_text("\n".join(persona_story_page_lines) + "\n", encoding="utf-8")
    feature_path.write_text("\n".join(feature_coverage_lines) + "\n", encoding="utf-8")
    return [psp_path, feature_path]
