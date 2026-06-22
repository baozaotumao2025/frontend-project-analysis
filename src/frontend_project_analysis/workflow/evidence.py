"""Evidence inventory and coverage helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.domain import ArtifactStatus
from ..models import Artifact, Project
from .state.definitions import WorkflowStateError


@dataclass(frozen=True)
class EvidenceItem:
    ref: str
    role: str
    disposition: str
    reason: str
    status: str
    source_path: str | None
    source_exists: bool
    has_version: bool

    @property
    def is_required(self) -> bool:
        return self.disposition != "excluded"

    @property
    def is_complete(self) -> bool:
        return self.disposition == "mapped"


@dataclass(frozen=True)
class EvidenceSnapshot:
    inventory: tuple[EvidenceItem, ...]

    @property
    def complete(self) -> bool:
        return all(item.disposition != "needs_review" for item in self.inventory)

    @property
    def unresolved_refs(self) -> tuple[str, ...]:
        return tuple(item.ref for item in self.inventory if item.disposition == "needs_review")


def artifact_ref(artifact: Artifact) -> str:
    return f"{artifact.artifact_type.value}:{artifact.slug}"


def _source_exists(root: Path, source_path: str | None) -> bool:
    if not source_path:
        return False
    return (root / source_path).exists()


def build_semantic_evidence_snapshot(
    session: Session,
    project: Project,
    artifact: Artifact,
) -> EvidenceSnapshot:
    root = Path(project.root_path)
    items: list[EvidenceItem] = []

    def append_item(
        *,
        target: Artifact,
        role: str,
        disposition: str,
        reason: str,
    ) -> None:
        items.append(
            EvidenceItem(
                ref=artifact_ref(target),
                role=role,
                disposition=disposition,
                reason=reason,
                status=target.status.value,
                source_path=target.source_path,
                source_exists=_source_exists(root, target.source_path),
                has_version=target.current_version is not None,
            )
        )

    focus_source_exists = _source_exists(root, artifact.source_path)
    if artifact.source_path and not focus_source_exists:
        raise WorkflowStateError(
            f"Cannot freeze semantic packet for {artifact_ref(artifact)} because the "
            f"source file '{artifact.source_path or '<missing>'}' is missing."
        )

    append_item(
        target=artifact,
        role="focus",
        disposition="mapped",
        reason="focus artifact is the review target",
    )

    for dependency in artifact.outgoing_dependencies:
        target = dependency.to_artifact
        source_exists = _source_exists(root, target.source_path)
        if dependency.is_hard:
            if target.source_path and not source_exists:
                disposition = "needs_review"
                reason = "hard dependency source file is missing"
            else:
                disposition = "mapped"
                if target.status == ArtifactStatus.APPROVED:
                    reason = "hard dependency is part of the frozen evidence set"
                else:
                    reason = "hard dependency is recorded in the evidence set"
        else:
            disposition = "excluded"
            reason = "soft dependency is outside the hard evidence boundary"
        append_item(
            target=target,
            role=f"dependency:{dependency.dependency_type.value}",
            disposition=disposition,
            reason=reason,
        )

    snapshot = EvidenceSnapshot(inventory=tuple(items))
    if snapshot.unresolved_refs:
        blocked = ", ".join(snapshot.unresolved_refs)
        raise WorkflowStateError(
            f"Cannot freeze semantic packet for {artifact_ref(artifact)} because the "
            f"evidence set is incomplete: {blocked}."
        )
    return snapshot
