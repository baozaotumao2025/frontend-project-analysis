"""Semantic review packet command."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ...core.config import get_paths, get_settings
from ...infrastructure.storage import session_scope
from ...repositories.dependencies import get_artifact_by_ref
from ...repositories.projects import get_project
from ...workflow import build_semantic_packet
from ...workflow.io import export_json_to_path
from ..utils import handle_service_error
from . import review_app
from .context import build_semantic_review_llm_context


@review_app.command("semantic-packet")
@handle_service_error
def review_semantic_packet(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        payload = build_semantic_packet(session, project_row, artifact_row)
    settings = get_settings()
    payload["llm"] = build_semantic_review_llm_context(settings)
    if output:
        export_json_to_path(payload, output)
        typer.echo(f"Wrote semantic packet to {output}")
    else:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))
