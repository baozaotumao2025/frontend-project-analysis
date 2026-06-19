"""Markdown scan import command."""

from __future__ import annotations

import json

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.io import import_markdown_files
from ..utils import handle_service_error
from . import import_app


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
    typer.echo(json.dumps({"apply": apply_changes, "files": preview}, indent=2, ensure_ascii=True))
