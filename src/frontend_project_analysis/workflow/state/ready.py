"""Ready-state helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ...core.domain import ArtifactStatus
from ...models import Artifact, ArtifactDependency, Project


def get_ready_artifacts(session: Session, project: Project) -> list[str]:
    from ...repositories.dependencies import artifact_ref

    artifacts = list(
        session.scalars(
            select(Artifact)
            .where(Artifact.project_id == project.id)
            .options(
                selectinload(Artifact.outgoing_dependencies).selectinload(
                    ArtifactDependency.to_artifact
                )
            )
        )
    )
    ready: list[str] = []
    for artifact in artifacts:
        if artifact.status not in {
            ArtifactStatus.DRAFT,
            ArtifactStatus.REJECTED,
            ArtifactStatus.STALE,
            ArtifactStatus.STRUCTURALLY_VALID,
        }:
            continue
        hard_dependencies = [dep for dep in artifact.outgoing_dependencies if dep.is_hard]
        if all(dep.to_artifact.status == ArtifactStatus.APPROVED for dep in hard_dependencies):
            ready.append(artifact_ref(artifact))
    return sorted(ready)
