"""Semantic review record command."""

from __future__ import annotations

from pathlib import Path

import typer

from ...core.config import get_paths
from ...core.domain import (
    ArtifactStatus,
    ReviewerKind,
    ReviewKind,
    semantic_review_to_artifact_status,
)
from ...infrastructure.storage import session_scope
from ...repositories.dependencies import get_artifact_by_ref
from ...repositories.projects import get_project
from ...repositories.reviews import record_review
from ...schemas import SemanticReviewPayload
from ...workflow import assert_artifact_status_in, transition_artifact
from ..utils import handle_service_error
from . import review_app


@review_app.command("semantic-record")
@handle_service_error
def review_semantic_record(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    input_path: Path = typer.Option(..., "--input"),
) -> None:
    payload = SemanticReviewPayload.model_validate_json(input_path.read_text(encoding="utf-8"))
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        assert_artifact_status_in(
            artifact_row,
            {
                ArtifactStatus.STRUCTURALLY_VALID,
                ArtifactStatus.SEMANTIC_REVIEW,
            },
            "record semantic review for",
        )
        record_review(
            session=session,
            artifact=artifact_row,
            review_kind=ReviewKind.SEMANTIC,
            review_status=payload.decision,
            reviewer_kind=ReviewerKind.LLM,
            summary=payload.summary,
            reviewer_ref=payload.reviewer_ref,
            payload={"model": payload.model},
            findings=[
                {
                    "severity": finding.severity,
                    "code": finding.code,
                    "message": finding.message,
                    "details": finding.details,
                }
                for finding in payload.findings
            ],
        )
        next_status = semantic_review_to_artifact_status(
            payload.decision,
            auto_approve=False,
        )
        transition_artifact(
            session=session,
            artifact=artifact_row,
            to_status=next_status,
            actor=payload.reviewer_ref,
            reason="Semantic review recorded.",
        )
        session.commit()
    typer.echo(f"Recorded semantic review for {artifact}")
