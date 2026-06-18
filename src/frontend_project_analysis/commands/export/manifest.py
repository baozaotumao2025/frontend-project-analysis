"""Manifest export command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.io import export_json_to_path, export_manifest
from ..utils import handle_service_error
from . import export_app


@export_app.command("manifest")
@handle_service_error
def export_manifest_cmd(project: str = typer.Option(..., "--project")) -> None:
    paths = get_paths()
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        payload = export_manifest(session, project_row)
    typer.echo(export_json_to_path(payload, paths.export_dir / f"{project}.json"))
