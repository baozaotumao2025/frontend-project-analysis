"""Artifact ready-state command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow import get_ready_artifacts
from ..utils import handle_service_error
from . import artifact_app


@artifact_app.command("ready")
@handle_service_error
def artifact_ready(project: str = typer.Option(..., "--project")) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        ready = get_ready_artifacts(session, project_row)
    for ref in ready:
        typer.echo(ref)
