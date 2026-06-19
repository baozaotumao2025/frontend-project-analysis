"""Artifact dependency repository helpers."""

from __future__ import annotations

from collections.abc import Iterable
from graphlib import CycleError, TopologicalSorter

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from ..core.domain import ArtifactStatus, ArtifactType, DependencyType
from ..infrastructure.logging_utils import get_logger
from ..models import Artifact, ArtifactDependency, ArtifactTransition, Project
from ..workflow.state import assert_transition_allowed, mark_dependents_stale
from .errors import RepositoryError

logger = get_logger(__name__)


def artifact_ref(artifact: Artifact) -> str:
    return f"{artifact.artifact_type.value}:{artifact.slug}"


def parse_artifact_ref(value: str) -> tuple[ArtifactType, str]:
    try:
        type_text, slug = value.split(":", 1)
        return ArtifactType(type_text), slug
    except ValueError as exc:
        raise RepositoryError(
            f"Artifact reference must look like 'feature:task-comments', got '{value}'."
        ) from exc


def get_artifact_by_ref(session: Session, project: Project, ref: str) -> Artifact:
    artifact_type, slug = parse_artifact_ref(ref)
    artifact = session.scalar(
        select(Artifact).where(
            and_(
                Artifact.project_id == project.id,
                Artifact.artifact_type == artifact_type,
                Artifact.slug == slug,
            )
        )
    )
    if artifact is None:
        raise RepositoryError(f"Artifact '{ref}' was not found in project '{project.key}'.")
    return artifact


def add_dependency(
    session: Session,
    project: Project,
    from_ref: str,
    to_ref: str,
    dependency_type: DependencyType,
    is_hard: bool,
) -> ArtifactDependency:
    from_artifact = get_artifact_by_ref(session, project, from_ref)
    to_artifact = get_artifact_by_ref(session, project, to_ref)
    dependency = session.scalar(
        select(ArtifactDependency).where(
            and_(
                ArtifactDependency.from_artifact_id == from_artifact.id,
                ArtifactDependency.to_artifact_id == to_artifact.id,
                ArtifactDependency.dependency_type == dependency_type,
            )
        )
    )
    if dependency is None:
        dependency = ArtifactDependency(
            from_artifact_id=from_artifact.id,
            to_artifact_id=to_artifact.id,
            dependency_type=dependency_type,
            is_hard=is_hard,
        )
        session.add(dependency)
        session.flush()
        logger.info(
            "Linked dependency %s -> %s (%s, hard=%s)",
            from_ref,
            to_ref,
            dependency_type.value,
            is_hard,
        )
        if is_hard and from_artifact.status == ArtifactStatus.APPROVED:
            assert_transition_allowed(from_artifact.status, ArtifactStatus.STALE)
            from_artifact.status = ArtifactStatus.STALE
            session.add(
                ArtifactTransition(
                    artifact_id=from_artifact.id,
                    from_status=ArtifactStatus.APPROVED.value,
                    to_status=ArtifactStatus.STALE.value,
                    reason=(
                        "approved artifact gained a new hard dependency "
                        f"on '{artifact_ref(to_artifact)}'"
                    ),
                    actor="dependency-link",
                )
            )
            mark_dependents_stale(session, from_artifact, actor="dependency-link")
    assert_no_cycles(session, project)
    return dependency


def list_artifacts(session: Session, project: Project) -> list[Artifact]:
    stmt = (
        select(Artifact)
        .where(Artifact.project_id == project.id)
        .options(selectinload(Artifact.outgoing_dependencies))
        .order_by(Artifact.round, Artifact.artifact_type, Artifact.slug)
    )
    return list(session.scalars(stmt))


def build_dependency_graph(artifacts: Iterable[Artifact]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for artifact in artifacts:
        ref = artifact_ref(artifact)
        graph.setdefault(ref, set())
        for dependency in artifact.outgoing_dependencies:
            graph[ref].add(artifact_ref(dependency.to_artifact))
    return graph


def assert_no_cycles(session: Session, project: Project) -> None:
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
    graph = build_dependency_graph(artifacts)
    sorter = TopologicalSorter(graph)
    try:
        tuple(sorter.static_order())
    except CycleError as exc:
        raise RepositoryError(f"Dependency cycle detected: {exc.args[1]}") from exc
