"""Graph JSON export command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.io import build_graph_projection, export_json_to_path
from ..utils import handle_service_error
from . import export_app


@export_app.command("graph-json")
@handle_service_error
def export_graph_json_cmd(project: str = typer.Option(..., "--project")) -> None:
    paths = get_paths()
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        payload = build_graph_projection(session, project_row, paths.root)
    typer.echo(export_json_to_path(payload, paths.export_dir / f"{project}-graph.json"))
