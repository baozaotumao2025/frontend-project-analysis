"""Round gate checks for workflow progression."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.domain import ROUND_BY_TYPE, ArtifactStatus, ArtifactType, WorkflowMode
from ..models import Artifact, Project
from .state.definitions import WorkflowStateError

ROUND_INPUT_TYPE: dict[int, ArtifactType] = {
    round_number + 1: artifact_type for artifact_type, round_number in ROUND_BY_TYPE.items()
}


@dataclass(frozen=True)
class RoundGateResult:
    round_number: int
    project_key: str
    mode: WorkflowMode
    input_type: ArtifactType | None
    checked_count: int
    blocked_refs: tuple[str, ...]
    evidence_complete: bool = True

    @property
    def passed(self) -> bool:
        if self.input_type is None:
            return True
        if self.mode == WorkflowMode.EXPLORE:
            return self.checked_count > 0
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


def evaluate_round_gate(
    session: Session,
    project: Project,
    round_number: int,
    mode: WorkflowMode = WorkflowMode.FORMAL,
) -> RoundGateResult:
    input_type = get_round_input_type(round_number)
    if input_type is None:
        return RoundGateResult(
            round_number=round_number,
            project_key=project.key,
            mode=mode,
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
    root = Path(project.root_path)
    blocked: list[str] = []
    for artifact in artifacts:
        issues: list[str] = []
        if artifact.status != ArtifactStatus.APPROVED:
            issues.append(artifact.status.value)
        if artifact.source_path:
            source_path = root / artifact.source_path
            if not source_path.exists():
                issues.append(f"missing source file '{artifact.source_path}'")
        if issues:
            blocked.append(f"{_artifact_ref(artifact)} ({'; '.join(issues)})")
    return RoundGateResult(
        round_number=round_number,
        project_key=project.key,
        mode=mode,
        input_type=input_type,
        checked_count=len(artifacts),
        blocked_refs=tuple(blocked),
        evidence_complete=not blocked,
    )


def assert_round_gate(
    session: Session,
    project: Project,
    round_number: int,
    mode: WorkflowMode = WorkflowMode.FORMAL,
) -> RoundGateResult:
    result = evaluate_round_gate(session, project, round_number, mode=mode)
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
        f"following {result.input_type.value} revisions are not approved or have missing "
        f"source files: {blocked}."
    )
