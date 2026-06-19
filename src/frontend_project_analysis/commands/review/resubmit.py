"""Unified review resubmission command."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import typer

from ...core.config import get_paths, get_settings
from ...core.domain import (
    ArtifactStatus,
    ReviewerKind,
    ReviewKind,
    ReviewStatus,
    semantic_review_to_artifact_status,
)
from ...infrastructure.storage import session_scope
from ...llm import run_semantic_review
from ...llm.validation import enforce_semantic_review_guard
from ...repositories.dependencies import get_artifact_by_ref
from ...repositories.projects import get_project
from ...repositories.reviews import record_review
from ...schemas import SemanticReviewPayload
from ...workflow import build_semantic_packet, run_structural_checks, transition_artifact
from ...workflow.io import export_json_to_path, import_markdown_files
from ..utils import handle_service_error
from . import review_app
from .context import build_semantic_review_llm_context, is_host_review_mode


def _default_packet_output(paths, artifact_ref: str) -> Path:
    safe_ref = artifact_ref.replace(":", "-")
    return paths.export_dir / f"{safe_ref}-resubmit-semantic-packet.json"


def _record_structural_review(session, artifact, findings: list) -> None:
    record_review(
        session=session,
        artifact=artifact,
        review_kind=ReviewKind.STRUCTURAL,
        review_status=ReviewStatus.PASSED if not findings else ReviewStatus.FAILED,
        reviewer_kind=ReviewerKind.RULE_ENGINE,
        summary="Structural review completed.",
        reviewer_ref="rule-engine",
        payload={"finding_count": len(findings), "source": "review resubmit"},
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


def _record_semantic_review(session, artifact, payload: SemanticReviewPayload) -> None:
    record_review(
        session=session,
        artifact=artifact,
        review_kind=ReviewKind.SEMANTIC,
        review_status=payload.decision,
        reviewer_kind=ReviewerKind.LLM,
        summary=payload.summary,
        reviewer_ref=payload.reviewer_ref,
        payload={
            "decision": payload.decision.value,
            "model": payload.model,
            "counterexamples": payload.counterexamples,
            "source": "review resubmit",
        },
        findings=[
            {
                "severity": finding.severity,
                "code": finding.code,
                "message": finding.message,
                "evidence": finding.evidence,
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
        artifact=artifact,
        to_status=next_status,
        actor=payload.reviewer_ref,
        reason="Semantic review resubmitted.",
    )


@review_app.command("resubmit")
@handle_service_error
def review_resubmit(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    review_input: Path | None = typer.Option(
        None,
        "--review-input",
        help="JSON review result produced by a fresh reviewer context.",
    ),
    packet_output: Path | None = typer.Option(
        None,
        "--packet-output",
        help="Where to write the frozen semantic review packet when host review is pending.",
    ),
) -> None:
    settings = get_settings()
    paths = get_paths()
    trace_id = uuid4().hex
    request_id = uuid4().hex
    with session_scope(paths) as session:
        project_row = get_project(session, project)
        import_markdown_files(session, project_row, paths.root, apply_changes=True)

        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        structural_findings = run_structural_checks(session, project_row, target_ref=artifact)
        _record_structural_review(session, artifact_row, structural_findings)
        if structural_findings:
            session.commit()
            for finding in structural_findings:
                prefix = f"{finding.artifact_ref}: " if finding.artifact_ref else ""
                typer.secho(
                    f"{finding.severity} {prefix}{finding.code} {finding.message}",
                    fg=typer.colors.RED,
                    err=True,
                )
            raise typer.Exit(1)

        if artifact_row.status != ArtifactStatus.STRUCTURALLY_VALID:
            transition_artifact(
                session=session,
                artifact=artifact_row,
                to_status=ArtifactStatus.STRUCTURALLY_VALID,
                actor="rule-engine",
                reason="Structural review passed during resubmit.",
            )
            session.flush()

        packet = build_semantic_packet(session, project_row, artifact_row)
        packet["llm"] = build_semantic_review_llm_context(settings)
        packet["trace_id"] = trace_id
        packet["request_id"] = request_id

        if review_input is not None:
            payload = SemanticReviewPayload.model_validate_json(
                review_input.read_text(encoding="utf-8")
            )
            payload = enforce_semantic_review_guard(payload)
            _record_semantic_review(session, artifact_row, payload)
            session.commit()
            typer.echo(f"Resubmitted {artifact}")
            return

        if is_host_review_mode(settings):
            output = packet_output or _default_packet_output(paths, artifact)
            export_json_to_path(packet, output)
            session.commit()
            typer.secho(
                "Host review packet written to "
                f"{output}. Use a fresh reviewer context to review it, then pass the "
                "result back with `fpa review resubmit --review-input <path>`.",
                fg=typer.colors.YELLOW,
                err=True,
            )
            typer.echo(f"Prepared resubmission packet for {artifact}")
            return

        provider_response = run_semantic_review(packet, settings=settings)
        payload = enforce_semantic_review_guard(provider_response.payload)
        _record_semantic_review(session, artifact_row, payload)
        session.commit()
    typer.echo(f"Resubmitted {artifact}")
