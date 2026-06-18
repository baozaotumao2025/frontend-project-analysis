"""Artifact version repository helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..core.domain import ROUND_BY_TYPE, ArtifactStatus, ArtifactType
from ..infrastructure.documents import compute_content_hash, read_document
from ..infrastructure.logging_utils import get_logger
from ..models import Artifact, ArtifactTransition, ArtifactVersion, Project
from ..workflow.state import WorkflowStateError, assert_transition_allowed, mark_dependents_stale

logger = get_logger(__name__)


def upsert_artifact(
    session: Session,
    project: Project,
    artifact_type: ArtifactType,
    slug: str,
    title: str,
    source_path: str | None,
    status: ArtifactStatus,
    metadata: dict,
    created_by: str = "system",
) -> Artifact:
    if status != ArtifactStatus.DRAFT:
        raise WorkflowStateError(
            "Artifacts can only be created or imported as 'draft'. "
            "Use review commands to advance lifecycle state."
        )
    stmt = select(Artifact).where(
        and_(
            Artifact.project_id == project.id,
            Artifact.artifact_type == artifact_type,
            Artifact.slug == slug,
        )
    )
    artifact = session.scalar(stmt)
    if artifact is None:
        artifact = Artifact(
            project_id=project.id,
            artifact_type=artifact_type,
            slug=slug,
            title=title,
            round=ROUND_BY_TYPE[artifact_type],
            status=ArtifactStatus.DRAFT,
            source_path=source_path,
            metadata_json=metadata,
        )

        session.add(artifact)
        session.flush()
        session.add(
            ArtifactTransition(
                artifact_id=artifact.id,
                from_status="",
                to_status=ArtifactStatus.DRAFT.value,
                reason="artifact created",
                actor=created_by,
            )
        )
        logger.info("Created artifact %s:%s", artifact_type.value, slug)
    else:
        previous_status = artifact.status
        previous_version = artifact.current_version
        old_status = artifact.status.value
        artifact.title = title
        artifact.source_path = source_path
        artifact.metadata_json = metadata

        artifact.round = ROUND_BY_TYPE[artifact_type]
        version = create_version_for_artifact(session, artifact, created_by=created_by)
        content_changed = previous_version is None or previous_version.content_hash != version.content_hash

        if content_changed:
            next_status = (
                ArtifactStatus.STALE
                if previous_status == ArtifactStatus.APPROVED
                else ArtifactStatus.DRAFT
            )
            if artifact.status != next_status:
                assert_transition_allowed(artifact.status, next_status)
                artifact.status = next_status
                session.add(
                    ArtifactTransition(
                        artifact_id=artifact.id,
                        from_status=old_status,
                        to_status=next_status.value,
                        reason=(
                            "approved artifact content changed"
                            if next_status == ArtifactStatus.STALE
                            else "artifact content changed"
                        ),
                        actor=created_by,
                    )
                )
                logger.info(
                    "Reset artifact %s:%s to %s after content change",
                    artifact_type.value,
                    slug,
                    next_status.value,
                )
            if next_status == ArtifactStatus.STALE:
                mark_dependents_stale(session, artifact, actor=created_by)
                logger.info(
                    "Marked artifact %s:%s stale after content change",
                    artifact_type.value,
                    slug,
                )
    return artifact


def create_version_for_artifact(
    session: Session,
    artifact: Artifact,
    created_by: str = "system",
) -> ArtifactVersion:
    body = ""
    metadata = dict(artifact.metadata_json or {})
    if artifact.source_path:
        source = Path(artifact.project.root_path) / artifact.source_path
        if source.exists():
            metadata_from_file, body = read_document(source)
            metadata = metadata_from_file or metadata
    content_hash = compute_content_hash(metadata, body)
    version_count = session.scalar(
        select(func.count())
        .select_from(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == artifact.id)
    )
    version = ArtifactVersion(
        artifact_id=artifact.id,
        version_no=(version_count or 0) + 1,
        content_hash=content_hash,
        metadata_json=metadata,
        body_snapshot=body,
        created_by=created_by,
    )
    session.add(version)
    session.flush()
    artifact.current_version_id = version.id
    return version
