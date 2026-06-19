"""Workflow gate and transition validation helpers."""

from __future__ import annotations

from collections.abc import Iterable

from ...core.domain import ArtifactStatus
from ...models import Artifact
from .definitions import WorkflowStateError

ALLOWED_TRANSITIONS: dict[ArtifactStatus, set[ArtifactStatus]] = {
    ArtifactStatus.DRAFT: {
        ArtifactStatus.STRUCTURALLY_VALID,
        ArtifactStatus.REJECTED,
    },
    ArtifactStatus.STRUCTURALLY_VALID: {
        ArtifactStatus.DRAFT,
        ArtifactStatus.SEMANTIC_REVIEW,
        ArtifactStatus.APPROVED,
        ArtifactStatus.REJECTED,
    },
    ArtifactStatus.SEMANTIC_REVIEW: {
        ArtifactStatus.DRAFT,
        ArtifactStatus.SEMANTIC_REVIEW,
        ArtifactStatus.APPROVED,
        ArtifactStatus.REJECTED,
    },
    ArtifactStatus.APPROVED: {
        ArtifactStatus.APPROVED,
        ArtifactStatus.REJECTED,
        ArtifactStatus.STALE,
        ArtifactStatus.SUPERSEDED,
    },
    ArtifactStatus.REJECTED: {
        ArtifactStatus.DRAFT,
        ArtifactStatus.STRUCTURALLY_VALID,
        ArtifactStatus.REJECTED,
    },
    ArtifactStatus.STALE: {
        ArtifactStatus.DRAFT,
        ArtifactStatus.REJECTED,
        ArtifactStatus.STRUCTURALLY_VALID,
    },
    ArtifactStatus.SUPERSEDED: {
        ArtifactStatus.ARCHIVED,
    },
    ArtifactStatus.ARCHIVED: set(),
}


def assert_transition_allowed(from_status: ArtifactStatus, to_status: ArtifactStatus) -> None:
    """Raise when a lifecycle transition is not allowed."""

    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise WorkflowStateError(
            f"Transition from '{from_status.value}' to '{to_status.value}' is not allowed."
        )


def assert_artifact_status_in(
    artifact: Artifact,
    allowed_statuses: Iterable[ArtifactStatus],
    action: str,
) -> None:
    """Require an artifact to be in one of the allowed lifecycle states."""

    from ...repositories.dependencies import artifact_ref

    allowed = tuple(allowed_statuses)
    if artifact.status in allowed:
        return
    expected = ", ".join(status.value for status in allowed)
    raise WorkflowStateError(
        f"Cannot {action} {artifact_ref(artifact)} while it is '{artifact.status.value}'. "
        f"Expected one of: {expected}."
    )


def assert_artifact_can_be_approved(artifact: Artifact) -> None:
    """Require an artifact to have fresh hard dependencies before approval.

    Approval is the point where a revision becomes fresh and publishable, so we
    reject the transition if any hard dependency is no longer approved.
    """

    from ...repositories.dependencies import artifact_ref

    blocked_refs = [
        f"{artifact_ref(dependency.to_artifact)} ({dependency.to_artifact.status.value})"
        for dependency in artifact.outgoing_dependencies
        if dependency.is_hard and dependency.to_artifact.status != ArtifactStatus.APPROVED
    ]
    if blocked_refs:
        blocked = ", ".join(blocked_refs)
        raise WorkflowStateError(
            f"Cannot approve {artifact_ref(artifact)} because hard dependencies are not "
            f"approved: {blocked}."
        )
