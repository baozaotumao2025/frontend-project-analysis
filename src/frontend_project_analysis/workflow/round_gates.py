"""Round gate checks for workflow progression."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.domain import ROUND_BY_TYPE, ArtifactStatus, ArtifactType
from ..models import Artifact, Project
from .state.definitions import WorkflowStateError

ROUND_INPUT_TYPE: dict[int, ArtifactType] = {
    round_number + 1: artifact_type for artifact_type, round_number in ROUND_BY_TYPE.items()
}


@dataclass(frozen=True)
class RoundGateResult:
    round_number: int
    project_key: str
    input_type: ArtifactType | None
    checked_count: int
    blocked_refs: tuple[str, ...]

    @property
    def passed(self) -> bool:
        if self.input_type is None:
            return True
        return self.checked_count > 0 and not self.blocked_refs


def _artifact_ref(artifact: Artifact) -> str:
    return f"{artifact.artifact_type.value}:{artifact.slug}"


def get_round_input_type(round_number: int) -> ArtifactType | None:
    if round_number <= 1:
        return None
    try:
        return ROUND_INPUT_TYPE[round_number]
    except KeyError as exc:
        raise WorkflowStateError(f"Unsupported round '{round_number}'. Expected 1-6.") from exc


def evaluate_round_gate(session: Session, project: Project, round_number: int) -> RoundGateResult:
    input_type = get_round_input_type(round_number)
    if input_type is None:
        return RoundGateResult(
            round_number=round_number,
            project_key=project.key,
            input_type=None,
            checked_count=0,
            blocked_refs=(),
        )

    artifacts = list(
        session.scalars(
            select(Artifact)
            .where(
                Artifact.project_id == project.id,
                Artifact.artifact_type == input_type,
            )
            .order_by(Artifact.slug)
        )
    )
    blocked_refs = tuple(
        f"{_artifact_ref(artifact)} ({artifact.status.value})"
        for artifact in artifacts
        if artifact.status != ArtifactStatus.APPROVED
    )
    return RoundGateResult(
        round_number=round_number,
        project_key=project.key,
        input_type=input_type,
        checked_count=len(artifacts),
        blocked_refs=blocked_refs,
    )


def assert_round_gate(session: Session, project: Project, round_number: int) -> RoundGateResult:
    result = evaluate_round_gate(session, project, round_number)
    if result.passed:
        return result

    if result.checked_count == 0:
        raise WorkflowStateError(
            f"Round {round_number} cannot start for project '{project.key}' because no "
            f"{result.input_type.value if result.input_type else 'upstream'} revisions exist yet."
        )

    blocked = ", ".join(result.blocked_refs)
    raise WorkflowStateError(
        f"Round {round_number} cannot start for project '{project.key}' because the "
        f"following {result.input_type.value} revisions are not approved: {blocked}."
    )
