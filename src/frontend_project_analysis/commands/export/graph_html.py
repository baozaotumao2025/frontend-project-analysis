"""Graph HTML export command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.io import build_graph_projection, render_graph_html
from ..utils import handle_service_error
from . import export_app


@export_app.command("graph-html")
@handle_service_error
def export_graph_html_cmd(project: str = typer.Option(..., "--project")) -> None:
    paths = get_paths()
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        payload = build_graph_projection(session, project_row, paths.root)
    destination = paths.root / "analysis" / "relations" / "graph.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_graph_html(payload), encoding="utf-8")
    typer.echo(str(destination))
