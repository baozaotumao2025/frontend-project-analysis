from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from frontend_project_analysis.cli import app
from frontend_project_analysis.core.config import STATE_DIR_NAME, AppPaths, reset_settings_cache
from frontend_project_analysis.core.domain import ReviewStatus
from frontend_project_analysis.infrastructure.storage import initialize_database
from frontend_project_analysis.llm.types import ProviderResponse
from frontend_project_analysis.schemas import ProviderAuditPayload, SemanticReviewPayload

runner = CliRunner()


def prepare_project_root(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)


def prepare_brief_source(tmp_path: Path) -> Path:
    brief_path = tmp_path.parent / f"{tmp_path.name}-project-brief.md"
    brief_path.write_text(
        "# Project Brief\n\n"
        "## What does the product do?\n"
        "- Manage customer assignments.\n\n"
        "## Who are the main users?\n"
        "- Sales reps and operations leads.\n\n"
        "## What are the core usage scenarios?\n"
        "- Reassign customers and review ownership boundaries.\n",
        encoding="utf-8",
    )
    return brief_path


def project_paths(tmp_path: Path) -> AppPaths:
    state_dir = tmp_path / STATE_DIR_NAME
    return AppPaths(
        root=tmp_path,
        state_dir=state_dir,
        db_path=state_dir / "state.db",
        backup_dir=state_dir / "backups",
        export_dir=state_dir / "exports",
        log_dir=state_dir / "logs",
        audit_dir=state_dir / "audits",
    )


def prepare_database(tmp_path: Path) -> AppPaths:
    prepare_project_root(tmp_path)
    paths = project_paths(tmp_path)
    initialize_database(paths)
    return paths


def invoke_with_root(tmp_path: Path, args: list[str]):
    reset_settings_cache()
    return runner.invoke(app, args, env={"FPA_ROOT_DIR": str(tmp_path)})


def bootstrap_project(tmp_path: Path) -> None:
    prepare_project_root(tmp_path)
    brief_source = prepare_brief_source(tmp_path)
    init_result = invoke_with_root(
        tmp_path,
        [
            "project",
            "init",
            "--project",
            "crm-web",
            "--name",
            "CRM Web",
            "--brief-file",
            str(brief_source),
        ],
    )
    assert init_result.exit_code == 0, init_result.output
    add_persona = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "add",
            "--project",
            "crm-web",
            "--type",
            "persona",
            "--slug",
            "sales-rep",
            "--title",
            "Sales Rep",
        ],
    )
    assert add_persona.exit_code == 0, add_persona.output
    add_feature = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "add",
            "--project",
            "crm-web",
            "--type",
            "feature",
            "--slug",
            "customer-assignment",
            "--title",
            "Customer Assignment",
        ],
    )
    assert add_feature.exit_code == 0, add_feature.output
    link_result = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "link",
            "--project",
            "crm-web",
            "--from",
            "feature:customer-assignment",
            "--to",
            "persona:sales-rep",
        ],
    )
    assert link_result.exit_code == 0, link_result.output


def prepare_feature_for_semantic_review(tmp_path: Path) -> None:
    persona_structural = invoke_with_root(
        tmp_path,
        [
            "review",
            "structural",
            "--project",
            "crm-web",
            "--artifact",
            "persona:sales-rep",
        ],
    )
    assert persona_structural.exit_code == 0, persona_structural.output

    persona_review_path = tmp_path / "persona-semantic-review.json"
    persona_review_path.write_text(
        json.dumps(
            {
                "decision": "passed",
                "summary": "Persona semantic review passed.",
                "reviewer_ref": "fake-llm",
                "model": "fake-model",
                "findings": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    persona_record = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-record",
            "--project",
            "crm-web",
            "--artifact",
            "persona:sales-rep",
            "--input",
            str(persona_review_path),
        ],
    )
    assert persona_record.exit_code == 0, persona_record.output

    persona_approve = invoke_with_root(
        tmp_path,
        [
            "review",
            "approve",
            "--project",
            "crm-web",
            "--artifact",
            "persona:sales-rep",
        ],
    )
    assert persona_approve.exit_code == 0, persona_approve.output

    feature_structural = invoke_with_root(
        tmp_path,
        [
            "review",
            "structural",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
        ],
    )
    assert feature_structural.exit_code == 0, feature_structural.output


def approve_feature(tmp_path: Path) -> None:
    feature_review_path = tmp_path / "feature-semantic-review.json"
    feature_review_path.write_text(
        json.dumps(
            {
                "decision": "passed",
                "summary": "Feature semantic review passed.",
                "reviewer_ref": "fake-llm",
                "model": "fake-model",
                "findings": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    feature_record = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-record",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
            "--input",
            str(feature_review_path),
        ],
    )
    assert feature_record.exit_code == 0, feature_record.output

    feature_approve = invoke_with_root(
        tmp_path,
        [
            "review",
            "approve",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
        ],
    )
    assert feature_approve.exit_code == 0, feature_approve.output


def fake_semantic_review_response(
    packet: dict,
    *,
    decision: ReviewStatus,
    summary: str,
) -> ProviderResponse:
    payload = SemanticReviewPayload(
        decision=decision,
        summary=summary,
        reviewer_ref="fake-llm",
        model="fake-model",
        findings=[],
    )
    audit = ProviderAuditPayload(
        trace_id=packet["trace_id"],
        request_id=packet["request_id"],
        provider_name="mock",
        endpoint="mock://semantic-review",
        call_status="completed",
        attempt_count=1,
        duration_ms=0,
        request_json={"packet": True},
        response_json={"payload": payload.model_dump()},
        events=[],
        model_name="fake-model",
    )
    return ProviderResponse(
        payload=payload,
        raw_response={"payload": payload.model_dump()},
        audit=audit,
    )
