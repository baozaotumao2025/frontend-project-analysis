"""Artifact and dependency repository helpers."""

from __future__ import annotations

from collections.abc import Iterable
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from .documents import compute_content_hash, read_document
from .domain import ROUND_BY_TYPE, ArtifactStatus, ArtifactType, DependencyType
from .errors import AppError
from .logging_utils import get_logger
from .models import (
    Artifact,
    ArtifactDependency,
    ArtifactTransition,
    ArtifactVersion,
    Project,
)

logger = get_logger(__name__)


class RepositoryError(AppError):
    """Raised when repository-level workflow operations fail."""


def artifact_ref(artifact: Artifact) -> str:
    return f"{artifact.artifact_type.value}:{artifact.slug}"


def ensure_project(session: Session, key: str, name: str, root_path: Path) -> Project:
    project = session.scalar(select(Project).where(Project.key == key))
    if project is None:
        project = Project(key=key, name=name, root_path=str(root_path))
        session.add(project)
        session.flush()
        logger.info("Created project '%s' at %s", key, root_path)
    return project


def get_project(session: Session, key: str) -> Project:
    project = session.scalar(select(Project).where(Project.key == key))
    if project is None:
        raise RepositoryError(f"Project '{key}' was not found. Run `fpa project init` first.")
    return project


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
            status=status,
            source_path=source_path,
            metadata_json=metadata,
        )
        session.add(artifact)
        session.flush()
        session.add(
            ArtifactTransition(
                artifact_id=artifact.id,
                from_status="",
                to_status=status.value,
                reason="artifact created",
                actor=created_by,
            )
        )
        logger.info("Created artifact %s:%s", artifact_type.value, slug)
    else:
        old_status = artifact.status.value
        artifact.title = title
        artifact.source_path = source_path
        artifact.metadata_json = metadata
        artifact.round = ROUND_BY_TYPE[artifact_type]
        if artifact.status != status:
            artifact.status = status
            session.add(
                ArtifactTransition(
                    artifact_id=artifact.id,
                    from_status=old_status,
                    to_status=status.value,
                    reason="artifact updated",
                    actor=created_by,
                )
            )
            logger.info(
                "Transitioned artifact %s:%s from %s to %s during upsert",
                artifact_type.value,
                slug,
                old_status,
                status.value,
            )
    create_version_for_artifact(session, artifact, created_by=created_by)
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
