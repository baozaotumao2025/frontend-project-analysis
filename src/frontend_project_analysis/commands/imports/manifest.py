"""Manifest import command."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.io import import_manifest_payload
from ..utils import handle_service_error
from . import import_app


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
