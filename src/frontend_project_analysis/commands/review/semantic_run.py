"""Semantic review execution command."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import typer

from ...core.config import get_paths, get_settings
from ...core.domain import (
    ArtifactStatus,
    ReviewerKind,
    ReviewKind,
    semantic_review_to_artifact_status,
)
from ...core.errors import ProviderError
from ...infrastructure.logging_utils import call_context
from ...infrastructure.storage import session_scope
from ...llm import run_semantic_review
from ...llm.validation import enforce_semantic_review_guard
from ...repositories.dependencies import get_artifact_by_ref
from ...repositories.projects import get_project
from ...repositories.reviews import record_provider_call_audit, record_review
from ...workflow import assert_artifact_status_in, build_semantic_packet, transition_artifact
from ...workflow.io import archive_provider_call
from ..utils import handle_service_error
from . import review_app
from .context import build_semantic_review_llm_context, is_host_review_mode


@review_app.command("semantic-run")
@handle_service_error
def review_semantic_run(
    project: str = typer.Option(..., "--project"),
    artifact: str = typer.Option(..., "--artifact"),
    output: Path | None = typer.Option(None, "--output"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    settings = get_settings()
    paths = get_paths()
    trace_id = uuid4().hex
    request_id = uuid4().hex
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        artifact_row = get_artifact_by_ref(session, project_row, artifact)
        assert_artifact_status_in(
            artifact_row,
            {
                # A semantic review may only start after structural validation.
                ArtifactStatus.STRUCTURALLY_VALID,
            },
            "run semantic review on",
        )
        packet = build_semantic_packet(session, project_row, artifact_row)
        packet["llm"] = build_semantic_review_llm_context(settings)
        packet["trace_id"] = trace_id
        packet["request_id"] = request_id

        if output:
            from ...workflow.io import export_json_to_path

            export_json_to_path(packet, output)

        if is_host_review_mode(settings):
            if output:
                typer.secho(
                    "Host review packet written to "
                    f"{output}. Review it in a fresh reviewer sub-agent context "
                    "(use `fork_context: false` in Codex when available), then "
                    "record the result with `fpa review semantic-record`.",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
            else:
                typer.echo(json.dumps(packet, indent=2, ensure_ascii=True))
                typer.secho(
                    "No external LLM is configured. Review the packet above in "
                    "a fresh reviewer sub-agent context (use `fork_context: false` "
                    "in Codex when available), then record the result with "
                    "`fpa review semantic-record`.",
                    fg=typer.colors.YELLOW,
                    err=True,
                )
            return

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

            payload = enforce_semantic_review_guard(provider_response.payload)
            if not dry_run:
                record_review(
                    session=session,
                    artifact=artifact_row,
                    review_kind=ReviewKind.SEMANTIC,
                    review_status=payload.decision,
                    reviewer_kind=ReviewerKind.LLM,
                    summary=payload.summary,
                    reviewer_ref=payload.reviewer_ref,
                    payload={
                        "decision": payload.decision.value,
                        "model": payload.model,
                        "provider": settings.llm_provider,
                        "counterexamples": payload.counterexamples,
                        "raw_response": provider_response.raw_response,
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
                    auto_approve=settings.semantic_review_auto_approve,
                )
                transition_artifact(
                    session=session,
                    artifact=artifact_row,
                    to_status=next_status,
                    actor=payload.reviewer_ref,
                    reason="Semantic review completed.",
                )
                session.commit()
    typer.echo(f"Recorded semantic review for {artifact}")
