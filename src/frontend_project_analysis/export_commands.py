"""Export command group."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import typer

from .command_utils import handle_service_error
from .config import get_paths
from .repositories import get_project
from .service import export_json_to_path, export_manifest, render_relations_markdown
from .storage import session_scope

export_app = typer.Typer(help="Export commands for manifests and matrix documents.")


def register_export_commands(app: typer.Typer) -> None:
    app.add_typer(export_app, name="export")


@export_app.command("manifest")
@handle_service_error
def export_manifest_cmd(
    project: str = typer.Option(..., "--project"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    paths = get_paths()
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        payload = export_manifest(session, project_row)
    destination = output or paths.export_dir / f"{project}-manifest.json"
    export_json_to_path(payload, destination)
    typer.echo(f"Wrote manifest to {destination}")


@export_app.command("relations")
@handle_service_error
def export_relations_cmd(project: str = typer.Option(..., "--project")) -> None:
    paths = get_paths()
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        exported = render_relations_markdown(session, project_row, paths.root)
    for path in exported:
        typer.echo(f"Wrote {path}")


@export_app.command("sql")
@handle_service_error
def export_sql_cmd(output: Path | None = typer.Option(None, "--output")) -> None:
    paths = get_paths()
    if not paths.db_path.exists():
        typer.secho("Database is not initialized.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    destination = output or paths.export_dir / "state.sql"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(paths.db_path) as connection:
        dump = "\n".join(connection.iterdump()) + "\n"
    destination.write_text(dump, encoding="utf-8")
    typer.echo(f"Wrote SQL dump to {destination}")
