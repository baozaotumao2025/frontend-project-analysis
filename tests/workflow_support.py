from __future__ import annotations

from pathlib import Path

from frontend_project_analysis.core.domain import ArtifactStatus, ArtifactType
from frontend_project_analysis.models import Artifact
from frontend_project_analysis.workflow import transition_artifact
from frontend_project_analysis.repositories.versions import upsert_artifact


def approve_artifact(session, artifact: Artifact) -> None:
    if artifact.status in {ArtifactStatus.DRAFT, ArtifactStatus.STALE, ArtifactStatus.REJECTED}:
        transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.STRUCTURALLY_VALID,
            actor="test",
            reason="structural checks passed",
        )
    if artifact.status in {
        ArtifactStatus.DRAFT,
        ArtifactStatus.STALE,
        ArtifactStatus.REJECTED,
        ArtifactStatus.STRUCTURALLY_VALID,
    }:
        transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.SEMANTIC_REVIEW,
            actor="test",
            reason="semantic review recorded",
        )
    if artifact.status in {
        ArtifactStatus.DRAFT,
        ArtifactStatus.STALE,
        ArtifactStatus.REJECTED,
        ArtifactStatus.STRUCTURALLY_VALID,
        ArtifactStatus.SEMANTIC_REVIEW,
    }:
        transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.APPROVED,
            actor="test",
            reason="approved for downstream use",
        )


def artifact_in_status(
    session,
    project,
    *,
    artifact_type: ArtifactType,
    slug: str,
    source_path: str | None = None,
    target_status: ArtifactStatus,
) -> Artifact:
    artifact = upsert_artifact(
        session=session,
        project=project,
        artifact_type=artifact_type,
        slug=slug,
        title=slug.replace("-", " ").title(),
        source_path=source_path,
        status=ArtifactStatus.DRAFT,
        metadata={},
        created_by="test",
    )
    if target_status == ArtifactStatus.DRAFT:
        return artifact
    if target_status == ArtifactStatus.STRUCTURALLY_VALID:
        return transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.STRUCTURALLY_VALID,
            actor="test",
            reason="reach structurally valid",
        )
    if target_status == ArtifactStatus.SEMANTIC_REVIEW:
        transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.STRUCTURALLY_VALID,
            actor="test",
            reason="reach structurally valid",
        )
        return transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.SEMANTIC_REVIEW,
            actor="test",
            reason="reach semantic review",
        )
    if target_status == ArtifactStatus.APPROVED:
        approve_artifact(session, artifact)
        return artifact
    if target_status == ArtifactStatus.REJECTED:
        return transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.REJECTED,
            actor="test",
            reason="reach rejected",
        )
    if target_status == ArtifactStatus.STALE:
        approve_artifact(session, artifact)
        if source_path is None:
            raise AssertionError("source_path is required to materialize a stale revision")
        source_file = Path(project.root_path) / source_path
        source_file.write_text("updated content", encoding="utf-8")
        return upsert_artifact(
            session=session,
            project=project,
            artifact_type=artifact_type,
            slug=slug,
            title=slug.replace("-", " ").title(),
            source_path=source_path,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
    if target_status == ArtifactStatus.SUPERSEDED:
        approve_artifact(session, artifact)
        return transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.SUPERSEDED,
            actor="test",
            reason="supersede revision",
        )
    if target_status == ArtifactStatus.ARCHIVED:
        approve_artifact(session, artifact)
        superseded = transition_artifact(
            session=session,
            artifact=artifact,
            to_status=ArtifactStatus.SUPERSEDED,
            actor="test",
            reason="supersede revision",
        )
        return transition_artifact(
            session=session,
            artifact=superseded,
            to_status=ArtifactStatus.ARCHIVED,
            actor="test",
            reason="archive revision",
        )
    raise AssertionError(f"Unsupported target status: {target_status}")
