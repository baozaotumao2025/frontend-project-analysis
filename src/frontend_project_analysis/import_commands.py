"""Import command group."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .command_utils import handle_service_error
from .config import get_paths
from .repositories import get_project
from .service import import_manifest_payload, import_markdown_files
from .storage import session_scope

import_app = typer.Typer(help="Import commands for manifests and Markdown sources.")


def register_import_commands(app: typer.Typer) -> None:
    app.add_typer(import_app, name="import")


@import_app.command("markdown-scan")
@handle_service_error
def import_markdown_scan(
    project: str = typer.Option(..., "--project"),
    apply_changes: bool = typer.Option(False, "--apply"),
) -> None:
    paths = get_paths()
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        preview = import_markdown_files(session, project_row, paths.root, apply_changes)
        if apply_changes:
            session.commit()
    typer.echo(
        json.dumps({"apply": apply_changes, "files": preview}, indent=2, ensure_ascii=True)
    )


@import_app.command("manifest")
@handle_service_error
def import_manifest_cmd(
    project: str = typer.Option(..., "--project"),
    input_path: Path = typer.Option(..., "--input"),
    apply_changes: bool = typer.Option(False, "--apply"),
) -> None:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        preview = import_manifest_payload(session, project_row, payload, apply_changes)
        if apply_changes:
            session.commit()
    typer.echo(json.dumps(preview, indent=2, ensure_ascii=True))
