"""Review lifecycle commands."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...core.domain import ArtifactStatus
from ...infrastructure.storage import session_scope
from ...repositories.dependencies import get_artifact_by_ref
from ...repositories.projects import get_project
from ...workflow import assert_artifact_status_in, transition_artifact
from ..utils import handle_service_error
from . import review_app


@review_app.command("approve")
@handle_service_error
def review_approve(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    actor: str = typer.Option("human-reviewer", "--actor"),
    reason: str = typer.Option("Approved after review.", "--reason"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        assert_artifact_status_in(
            artifact_row,
            {ArtifactStatus.SEMANTIC_REVIEW},
            "approve",
        )
        transition_artifact(
            session,
            artifact_row,
            ArtifactStatus.APPROVED,
            actor=actor,
            reason=reason,
        )
        session.commit()
    typer.echo(f"Approved {artifact}")


@review_app.command("reject")
@handle_service_error
def review_reject(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    actor: str = typer.Option("human-reviewer", "--actor"),
    reason: str = typer.Option("Rejected after review.", "--reason"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        assert_artifact_status_in(
            artifact_row,
            {
                ArtifactStatus.STRUCTURALLY_VALID,
                ArtifactStatus.SEMANTIC_REVIEW,
                ArtifactStatus.APPROVED,
                ArtifactStatus.STALE,
            },
            "reject",
        )
        transition_artifact(
            session,
            artifact_row,
            ArtifactStatus.REJECTED,
            actor=actor,
            reason=reason,
        )
        session.commit()
    typer.echo(f"Rejected {artifact}")
