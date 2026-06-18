"""Artifact dependency link command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...core.domain import DependencyType
from ...infrastructure.storage import session_scope
from ...repositories.dependencies import add_dependency
from ...repositories.projects import get_project
from ..utils import handle_service_error
from . import artifact_app


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
