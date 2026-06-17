"""Deterministic workflow checks and ready-state helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .domain import ArtifactStatus, ROUND_BY_TYPE, REQUIRED_FRONTMATTER_FIELDS
from .errors import AppError
from .models import Artifact, ArtifactDependency, Project
from .repository_artifacts import artifact_ref, assert_no_cycles, list_artifacts


class WorkflowStateError(AppError):
    """Raised when workflow state operations fail validation."""


@dataclass
class CheckFinding:
    severity: str
    code: str
    message: str
    artifact_ref: str | None = None


def get_ready_artifacts(session: Session, project: Project) -> list[str]:
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


def run_structural_checks(
    session: Session,
    project: Project,
    target_ref: str | None = None,
) -> list[CheckFinding]:
    artifacts = list_artifacts(session, project)
    artifact_map = {artifact_ref(item): item for item in artifacts}
    if target_ref and target_ref not in artifact_map:
        raise WorkflowStateError(
            f"Artifact '{target_ref}' was not found in project '{project.key}'."
        )
    selected = [artifact_map[target_ref]] if target_ref else artifacts
    findings: list[CheckFinding] = []

    try:
        assert_no_cycles(session, project)
    except WorkflowStateError as exc:
        findings.append(CheckFinding(severity="FAIL", code="dependency_cycle", message=str(exc)))

    for artifact in selected:
        ref = artifact_ref(artifact)
        if artifact.round != ROUND_BY_TYPE[artifact.artifact_type]:
            findings.append(
                CheckFinding(
                    severity="FAIL",
                    code="round_mismatch",
                    message=(
                        f"Round {artifact.round} does not match "
                        f"{artifact.artifact_type.value}."
                    ),
                    artifact_ref=ref,
                )
            )
        if artifact.source_path:
            source = Path(project.root_path) / artifact.source_path
            if not source.exists():
                findings.append(
                    CheckFinding(
                        severity="FAIL",
                        code="missing_source",
                        message=f"Source file '{artifact.source_path}' does not exist.",
                        artifact_ref=ref,
                    )
                )
            else:
                from .documents import read_document

                metadata, _body = read_document(source)
                missing = [field for field in REQUIRED_FRONTMATTER_FIELDS if field not in metadata]
                if missing:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="missing_frontmatter_fields",
                            message=f"Missing frontmatter fields: {', '.join(missing)}.",
                            artifact_ref=ref,
                        )
                    )
                if (
                    metadata.get("artifact_type")
                    and metadata["artifact_type"] != artifact.artifact_type.value
                ):
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="artifact_type_mismatch",
                            message=(
                                "Frontmatter artifact_type does not match "
                                "database artifact type."
                            ),
                            artifact_ref=ref,
                        )
                    )
                if metadata.get("slug") and metadata["slug"] != artifact.slug:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="slug_mismatch",
                            message="Frontmatter slug does not match database slug.",
                            artifact_ref=ref,
                        )
                    )
                if metadata.get("round") and int(metadata["round"]) != artifact.round:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="round_frontmatter_mismatch",
                            message="Frontmatter round does not match database round.",
                            artifact_ref=ref,
                        )
                    )
                if metadata.get("project") and metadata["project"] != project.key:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="project_mismatch",
                            message="Frontmatter project does not match selected project key.",
                            artifact_ref=ref,
                        )
                    )
        for dependency in artifact.outgoing_dependencies:
            if dependency.is_hard and artifact.status in {
                ArtifactStatus.STRUCTURALLY_VALID,
                ArtifactStatus.SEMANTIC_REVIEW,
                ArtifactStatus.APPROVED,
            } and dependency.to_artifact.status != ArtifactStatus.APPROVED:
                findings.append(
                    CheckFinding(
                        severity="FAIL",
                        code="unapproved_dependency",
                        message=(
                            "Hard dependency "
                            f"'{artifact_ref(dependency.to_artifact)}' is not approved."
                        ),
                        artifact_ref=ref,
                    )
                )
    return findings
