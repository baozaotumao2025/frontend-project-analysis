"""Artifact listing command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.dependencies import artifact_ref, list_artifacts
from ...repositories.projects import get_project
from ..utils import handle_service_error
from . import artifact_app


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
