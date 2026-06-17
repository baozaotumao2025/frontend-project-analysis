"""Review command group."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import typer

from .command_utils import handle_service_error
from .config import get_paths, get_settings, require_llm_settings
from .domain import ArtifactStatus, ReviewerKind, ReviewKind, ReviewStatus
from .errors import ProviderError
from .llm import run_semantic_review
from .logging_utils import call_context
from .repositories import (
    artifact_ref,
    get_artifact_by_ref,
    get_project,
    record_provider_call_audit,
    record_review,
)
from .schemas import SemanticReviewPayload
from .storage import session_scope
from .workflow_io import archive_provider_call, export_json_to_path
from .workflow_state import build_semantic_packet, run_structural_checks, transition_artifact

review_app = typer.Typer(help="Structural and semantic review commands.")


def register_review_commands(app: typer.Typer) -> None:
    app.add_typer(review_app, name="review")


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


@review_app.command("semantic-packet")
@handle_service_error
def review_semantic_packet(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    require_llm_settings()
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        payload = build_semantic_packet(session, project_row, artifact_row)
    settings = get_settings()
    payload["llm"] = {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "api_path": settings.llm_api_path,
        "timeout_seconds": settings.llm_timeout_seconds,
        "temperature": settings.llm_temperature,
        "organization": settings.llm_organization,
    }
    if output:
        export_json_to_path(payload, output)
        typer.echo(f"Wrote semantic packet to {output}")
    else:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=True))


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
        next_status = (
            ArtifactStatus.SEMANTIC_REVIEW
            if payload.decision == ReviewStatus.NEEDS_REVISION
            else ArtifactStatus.STRUCTURALLY_VALID
        )
        if payload.decision == ReviewStatus.PASSED:
            next_status = ArtifactStatus.SEMANTIC_REVIEW
        elif payload.decision == ReviewStatus.FAILED:
            next_status = ArtifactStatus.REJECTED
        transition_artifact(
            session=session,
            artifact=artifact_row,
            to_status=next_status,
            actor=payload.reviewer_ref,
            reason="Semantic review recorded.",
        )
        settings = get_settings()
        if payload.decision == ReviewStatus.PASSED and settings.semantic_review_auto_approve:
            transition_artifact(
                session=session,
                artifact=artifact_row,
                to_status=ArtifactStatus.APPROVED,
                actor="auto-approve",
                reason="Auto approved by semantic review policy.",
            )
        session.commit()
    typer.echo(f"Recorded semantic review for {artifact}")


@review_app.command("semantic-run")
@handle_service_error
def review_semantic_run(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    output: Path | None = typer.Option(None, "--output"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    settings = require_llm_settings()
    paths = get_paths()
    trace_id = uuid4().hex
    request_id = uuid4().hex
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        packet = build_semantic_packet(session, project_row, artifact_row)
        packet["llm"] = {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
            "api_path": settings.llm_api_path,
            "max_output_tokens": settings.llm_max_output_tokens,
            "timeout_seconds": settings.llm_timeout_seconds,
            "temperature": settings.llm_temperature,
            "organization": settings.llm_organization,
            "anthropic_version": settings.anthropic_version,
        }
        packet["trace_id"] = trace_id
        packet["request_id"] = request_id
        with call_context(trace_id=trace_id, request_id=request_id):
            try:
                provider_response = run_semantic_review(packet, settings=settings)
            except ProviderError as exc:
                if exc.audit_payload:
                    request_path, response_path = archive_provider_call(
                        paths=paths,
                        project_key=project_row.key,
                        artifact_ref_value=artifact,
                        audit_payload=exc.audit_payload,
                    )
                    record_provider_call_audit(
                        session=session,
                        artifact=artifact_row,
                        trace_id=exc.audit_payload.get("trace_id", trace_id),
                        request_id=exc.audit_payload.get("request_id", request_id),
                        provider_name=exc.audit_payload.get("provider_name", settings.llm_provider),
                        error_code=exc.audit_payload.get("error_code"),
                        model_name=exc.audit_payload.get("model_name", settings.llm_model),
                        endpoint=exc.audit_payload.get("endpoint", ""),
                        call_status=exc.audit_payload.get("call_status", "failed"),
                        attempt_count=exc.audit_payload.get("attempt_count", 0),
                        duration_ms=exc.audit_payload.get("duration_ms", 0),
                        request_path=str(request_path),
                        response_path=str(response_path) if response_path else None,
                        request_summary_json=exc.audit_payload.get("request_json", {}),
                        response_summary_json=exc.audit_payload.get("response_json") or {},
                        events_json=exc.audit_payload.get("events", []),
                        error_message=exc.audit_payload.get("error_message") or str(exc),
                    )
                    session.commit()
                raise

            if not dry_run:
                review = record_review(
                    session=session,
                    artifact=artifact_row,
                    review_kind=ReviewKind.SEMANTIC,
                    review_status=provider_response.payload.decision,
                    reviewer_kind=ReviewerKind.LLM,
                    summary=provider_response.payload.summary,
                    reviewer_ref=provider_response.payload.reviewer_ref,
                    payload={
                        "model": provider_response.payload.model,
                        "provider": settings.llm_provider,
                        "raw_response": provider_response.raw_response,
                    },
                    findings=[
                        {
                            "severity": finding.severity,
                            "code": finding.code,
                            "message": finding.message,
                            "details": finding.details,
                        }
                        for finding in provider_response.payload.findings
                    ],
                )
                request_path, response_path = archive_provider_call(
                    paths=paths,
                    project_key=project_row.key,
                    artifact_ref_value=artifact,
                    audit_payload=provider_response.audit.model_dump(),
                )
                record_provider_call_audit(
                    session=session,
                    artifact=artifact_row,
                    trace_id=provider_response.audit.trace_id,
                    request_id=provider_response.audit.request_id,
                    provider_name=provider_response.audit.provider_name,
                    error_code=provider_response.audit.error_code,
                    model_name=provider_response.audit.model_name,
                    endpoint=provider_response.audit.endpoint,
                    call_status=provider_response.audit.call_status,
                    attempt_count=provider_response.audit.attempt_count,
                    duration_ms=provider_response.audit.duration_ms,
                    request_path=str(request_path),
                    response_path=str(response_path) if response_path else None,
                    request_summary_json=provider_response.audit.request_json,
                    response_summary_json=provider_response.audit.response_json or {},
                    events_json=[event.model_dump() for event in provider_response.audit.events],
                    error_message=provider_response.audit.error_message,
                    review=review,
                )
                next_status = ArtifactStatus.SEMANTIC_REVIEW
                if provider_response.payload.decision == ReviewStatus.FAILED:
                    next_status = ArtifactStatus.REJECTED
                transition_artifact(
                    session=session,
                    artifact=artifact_row,
                    to_status=next_status,
                    actor=provider_response.payload.reviewer_ref,
                    reason="Semantic review executed via provider.",
                )
                if (
                    provider_response.payload.decision == ReviewStatus.PASSED
                    and settings.semantic_review_auto_approve
                ):
                    transition_artifact(
                        session=session,
                        artifact=artifact_row,
                        to_status=ArtifactStatus.APPROVED,
                        actor="auto-approve",
                        reason="Auto approved by semantic review policy.",
                    )
                session.commit()

    if output:
        export_json_to_path(provider_response.raw_response, output)
        typer.echo(f"Wrote provider response to {output}")
    typer.echo(provider_response.payload.model_dump_json(indent=2))


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
        transition_artifact(
            session,
            artifact_row,
            ArtifactStatus.REJECTED,
            actor=actor,
            reason=reason,
        )
        session.commit()
    typer.echo(f"Rejected {artifact}")
