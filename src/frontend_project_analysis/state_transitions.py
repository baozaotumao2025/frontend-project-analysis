"""Workflow transition helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .domain import ArtifactStatus
from .logging_utils import get_logger
from .models import Artifact, ArtifactDependency, ArtifactTransition
from .repository_artifacts import artifact_ref

logger = get_logger(__name__)


def transition_artifact(
    session: Session,
    artifact: Artifact,
    to_status: ArtifactStatus,
    actor: str,
    reason: str,
) -> Artifact:
    from_status = artifact.status.value
    artifact.status = to_status
    session.add(
        ArtifactTransition(
            artifact_id=artifact.id,
            from_status=from_status,
            to_status=to_status.value,
            actor=actor,
            reason=reason,
        )
    )
    logger.info(
        "Transitioned %s from %s to %s",
        artifact_ref(artifact),
        from_status,
        to_status.value,
    )
    if to_status == ArtifactStatus.APPROVED:
        mark_dependents_stale(session, artifact, actor=actor)
    return artifact


def mark_dependents_stale(session: Session, artifact: Artifact, actor: str) -> None:
    dependents = session.scalars(
        select(Artifact)
        .join(ArtifactDependency, ArtifactDependency.from_artifact_id == Artifact.id)
        .where(ArtifactDependency.to_artifact_id == artifact.id)
    )
    for dependent in dependents:
        if dependent.status == ArtifactStatus.APPROVED:
            session.add(
                ArtifactTransition(
                    artifact_id=dependent.id,
                    from_status=dependent.status.value,
                    to_status=ArtifactStatus.STALE.value,
                    actor=actor,
                    reason=f"Dependency '{artifact_ref(artifact)}' changed approval lineage.",
                )
            )
            dependent.status = ArtifactStatus.STALE
