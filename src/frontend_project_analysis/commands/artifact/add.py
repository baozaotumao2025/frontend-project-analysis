"""Artifact registration command."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...core.domain import ArtifactStatus, ArtifactType
from ...infrastructure.storage import initialize_database, session_scope
from ...repositories.dependencies import artifact_ref
from ...repositories.projects import get_project
from ...repositories.versions import upsert_artifact
from ..utils import handle_service_error
from . import artifact_app


@artifact_app.command("add")
@handle_service_error
def artifact_add(
    project: str = typer.Option(..., "--project"),
    artifact_type: ArtifactType = typer.Option(..., "--type"),
    slug: str = typer.Option(..., "--slug"),
    title: str = typer.Option(..., "--title"),
    source_path: str | None = typer.Option(None, "--source-path"),
) -> None:
    paths = get_paths()
    initialize_database(paths)
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        artifact = upsert_artifact(
            session=session,
            project=project_row,
            artifact_type=artifact_type,
            slug=slug,
            title=title,
            source_path=source_path,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="cli",
        )
        session.commit()
    typer.echo(f"Registered {artifact_ref(artifact)}")
