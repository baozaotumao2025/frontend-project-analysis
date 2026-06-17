"""Artifact command group."""

from __future__ import annotations

import typer

from .command_utils import handle_service_error
from .config import get_paths
from .domain import ArtifactStatus, ArtifactType, DependencyType
from .repositories import (
    add_dependency,
    artifact_ref,
    get_artifact_by_ref,
    get_project,
    list_artifacts,
    upsert_artifact,
)
from .storage import initialize_database, session_scope
from .workflow_state import get_ready_artifacts

artifact_app = typer.Typer(help="Artifact registration and dependency commands.")


def register_artifact_commands(app: typer.Typer) -> None:
    app.add_typer(artifact_app, name="artifact")


@artifact_app.command("add")
@handle_service_error
def artifact_add(
    project: str = typer.Option(..., "--project"),
    artifact_type: ArtifactType = typer.Option(..., "--type"),
    slug: str = typer.Option(..., "--slug"),
    title: str = typer.Option(..., "--title"),
    source_path: str | None = typer.Option(None, "--source-path"),
    status: ArtifactStatus = typer.Option(ArtifactStatus.DRAFT, "--status"),
) -> None:
    paths = get_paths()
    initialize_database(paths)
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        artifact = upsert_artifact(
            session=session,
            project=project_row,
            artifact_type=artifact_type,
            slug=slug,
            title=title,
            source_path=source_path,
            status=status,
            metadata={},
            created_by="cli",
        )
        session.commit()
    typer.echo(f"Registered {artifact_ref(artifact)}")


@artifact_app.command("link")
@handle_service_error
def artifact_link(
    project: str = typer.Option(..., "--project"),
    from_ref: str = typer.Option(..., "--from"),
    to_ref: str = typer.Option(..., "--to"),
    dependency_type: DependencyType = typer.Option(DependencyType.REQUIRES, "--type"),
    soft: bool = typer.Option(False, "--soft", help="Create a soft dependency edge."),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        dependency = add_dependency(
            session=session,
            project=project_row,
            from_ref=from_ref,
            to_ref=to_ref,
            dependency_type=dependency_type,
            is_hard=not soft,
        )
        session.commit()
    typer.echo(
        "Linked "
        f"{from_ref} -> {to_ref} as {dependency.dependency_type.value} "
        f"({'hard' if dependency.is_hard else 'soft'})"
    )


@artifact_app.command("list")
@handle_service_error
def artifact_list(project: str = typer.Option(..., "--project")) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        rows = list_artifacts(session, project_row)
        for row in rows:
            typer.echo(
                f"{artifact_ref(row)} [{row.status.value}] "
                f"round={row.round} path={row.source_path or '-'}"
            )


@artifact_app.command("ready")
@handle_service_error
def artifact_ready(project: str = typer.Option(..., "--project")) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        ready = get_ready_artifacts(session, project_row)
    for ref in ready:
        typer.echo(ref)
