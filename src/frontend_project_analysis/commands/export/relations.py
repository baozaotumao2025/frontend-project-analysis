"""Relations export command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.io import render_relations_markdown
from ..utils import handle_service_error
from . import export_app


@export_app.command("relations")
@handle_service_error
def export_relations_cmd(project: str = typer.Option(..., "--project")) -> None:
    paths = get_paths()
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        written = render_relations_markdown(session, project_row, paths.root)
    for path in written:
        typer.echo(str(path))
