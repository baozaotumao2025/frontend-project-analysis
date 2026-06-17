"""Project command group."""

from __future__ import annotations

import json

import typer

from .command_utils import handle_service_error
from .config import get_paths
from .repositories import ensure_project
from .service import initialize_project
from .storage import initialize_database, session_scope

project_app = typer.Typer(help="Project lifecycle commands.")


def register_project_commands(app: typer.Typer) -> None:
    app.add_typer(project_app, name="project")


@project_app.command("init")
@handle_service_error
def project_init(
    project: str = typer.Option(..., "--project"),
    name: str = typer.Option(..., "--name"),
) -> None:
    paths = get_paths()
    initialize_database(paths)
    payload = initialize_project(paths, project, name)
    with session_scope(paths) as session:
        ensure_project(session, project, name, paths.root)
        session.commit()
    typer.echo(json.dumps(payload, indent=2))
