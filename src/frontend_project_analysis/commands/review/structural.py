"""Structural review commands."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...core.domain import ArtifactStatus, ReviewerKind, ReviewKind, ReviewStatus
from ...infrastructure.storage import session_scope
from ...repositories.dependencies import get_artifact_by_ref
from ...repositories.projects import get_project
from ...repositories.reviews import record_review
from ...workflow import assert_artifact_status_in, run_structural_checks, transition_artifact
from ..utils import handle_service_error
from . import review_app


@review_app.command("structural")
@handle_service_error
def review_structural(
    project: str = typer.Option(..., "--project"),
    artifact: str | None = typer.Option(None, "--artifact"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        findings = run_structural_checks(session, project_row, target_ref=artifact)
        if artifact:
            target = get_artifact_by_ref(session, project_row, artifact)
            assert_artifact_status_in(
                target,
                {
                    ArtifactStatus.DRAFT,
                    ArtifactStatus.REJECTED,
                    ArtifactStatus.STALE,
                },
                "run structural review on",
            )
            record_review(
                session=session,
                artifact=target,
                review_kind=ReviewKind.STRUCTURAL,
                review_status=ReviewStatus.PASSED if not findings else ReviewStatus.FAILED,
                reviewer_kind=ReviewerKind.RULE_ENGINE,
                summary="Structural review completed.",
                reviewer_ref="rule-engine",
                payload={"finding_count": len(findings)},
                findings=[
                    {
                        "severity": finding.severity,
                        "code": finding.code,
                        "message": finding.message,
                        "details": {"artifact_ref": finding.artifact_ref},
                    }
                    for finding in findings
                ],
            )
            if not findings:
                transition_artifact(
                    session=session,
                    artifact=target,
                    to_status=ArtifactStatus.STRUCTURALLY_VALID,
                    actor="rule-engine",
                    reason="Structural review passed.",
                )
        session.commit()
    if findings:
        for finding in findings:
            prefix = f"{finding.artifact_ref}: " if finding.artifact_ref else ""
            typer.secho(
                f"{finding.severity} {prefix}{finding.code} {finding.message}",
                fg=typer.colors.RED,
                err=True,
            )
        raise typer.Exit(1)
    typer.echo("Structural review passed.")
