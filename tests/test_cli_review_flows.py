from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from frontend_project_analysis.core.domain import ArtifactStatus, ReviewStatus
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.llm.types import ProviderResponse
from frontend_project_analysis.models import ArtifactReview
from frontend_project_analysis.repositories.dependencies import get_artifact_by_ref
from frontend_project_analysis.repositories.projects import get_project
from tests.cli_support import (
    bootstrap_project,
    fake_semantic_review_response,
    invoke_with_root,
    prepare_feature_for_semantic_review,
    project_paths,
)

pytestmark = pytest.mark.smoke


def test_review_semantic_packet_and_exports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap_project(tmp_path)
    monkeypatch.setenv("FPA_LLM_PROVIDER", "host")

    packet_path = tmp_path / "semantic-packet.json"
    packet_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-packet",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
            "--output",
            str(packet_path),
        ],
    )
    assert packet_result.exit_code == 0, packet_result.output
    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["artifact"]["ref"] == "feature:customer-assignment"
    assert packet["llm"]["provider"] == "host"

    manifest_result = invoke_with_root(
        tmp_path,
        [
            "export",
            "manifest",
            "--project",
            "crm-web",
        ],
    )
    assert manifest_result.exit_code == 0, manifest_result.output
    manifest_path = tmp_path / ".frontend-project-analysis" / "exports" / "crm-web.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["project"]["key"] == "crm-web"
    assert any(item["ref"] == "feature:customer-assignment" for item in manifest["artifacts"])

    relations_result = invoke_with_root(
        tmp_path,
        [
            "export",
            "relations",
            "--project",
            "crm-web",
        ],
    )
    assert relations_result.exit_code == 0, relations_result.output
    psp_path = tmp_path / "analysis" / "relations" / "persona-story-page-matrix.md"
    feature_path = tmp_path / "analysis" / "relations" / "feature-coverage-matrix.md"
    assert psp_path.exists()
    assert feature_path.exists()
    assert "Persona Story Page Matrix" in psp_path.read_text(encoding="utf-8")
    assert "Feature Coverage Matrix" in feature_path.read_text(encoding="utf-8")
    assert "| Persona | Story Map | Page | Feature |" in psp_path.read_text(encoding="utf-8")
    assert "| Feature | Service Persona | Source Page | Covered Story |" in feature_path.read_text(
        encoding="utf-8"
    )


def test_review_semantic_run_updates_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

    from frontend_project_analysis.commands.review import semantic_run as semantic_run_module

    def fake_run_semantic_review(packet: dict, settings=None) -> ProviderResponse:
        return fake_semantic_review_response(
            packet,
            decision=ReviewStatus.FAILED,
            summary="Fake semantic review.",
        )

    monkeypatch.setattr(semantic_run_module, "run_semantic_review", fake_run_semantic_review)
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")

    run_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-run",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:customer-assignment")
        review = session.scalar(
            select(ArtifactReview).where(ArtifactReview.artifact_id == artifact_row.id)
        )
        assert artifact_row.status == ArtifactStatus.REJECTED
        assert review is not None


def test_review_semantic_run_host_mode_emits_packet_without_recording(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

    monkeypatch.setenv("FPA_LLM_PROVIDER", "host")

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:customer-assignment")
        review_count_before = len(
            session.scalars(
                select(ArtifactReview).where(ArtifactReview.artifact_id == artifact_row.id)
            ).all()
        )
        assert artifact_row.status == ArtifactStatus.STRUCTURALLY_VALID

    run_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-run",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
        ],
    )
    assert run_result.exit_code == 0, run_result.output
    assert '"provider": "host"' in run_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:customer-assignment")
        review_count_after = len(
            session.scalars(
                select(ArtifactReview).where(ArtifactReview.artifact_id == artifact_row.id)
            ).all()
        )
        assert artifact_row.status == ArtifactStatus.STRUCTURALLY_VALID
        assert review_count_after == review_count_before


def test_review_semantic_run_passed_waits_for_human_approval_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

    from frontend_project_analysis.commands.review import semantic_run as semantic_run_module

    def fake_run_semantic_review(packet: dict, settings=None) -> ProviderResponse:
        return fake_semantic_review_response(
            packet,
            decision=ReviewStatus.PASSED,
            summary="Semantic review passed.",
        )

    monkeypatch.setattr(semantic_run_module, "run_semantic_review", fake_run_semantic_review)

    run_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-run",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:customer-assignment")
        review = session.scalar(
            select(ArtifactReview).where(ArtifactReview.artifact_id == artifact_row.id)
        )
        assert artifact_row.status == ArtifactStatus.SEMANTIC_REVIEW
        assert review is not None


def test_review_semantic_run_passed_can_auto_approve(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

    from frontend_project_analysis.commands.review import semantic_run as semantic_run_module

    def fake_run_semantic_review(packet: dict, settings=None) -> ProviderResponse:
        return fake_semantic_review_response(
            packet,
            decision=ReviewStatus.PASSED,
            summary="Semantic review passed.",
        )

    monkeypatch.setattr(semantic_run_module, "run_semantic_review", fake_run_semantic_review)
    monkeypatch.setenv("FPA_SEMANTIC_REVIEW_AUTO_APPROVE", "true")

    run_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-run",
            "--project",
            "crm-web",
            "--artifact",
            "feature:customer-assignment",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:customer-assignment")
        review = session.scalar(
            select(ArtifactReview).where(ArtifactReview.artifact_id == artifact_row.id)
        )
        assert artifact_row.status == ArtifactStatus.APPROVED
        assert review is not None


def test_review_approve_rejects_stale_hard_dependencies(
    tmp_path: Path,
) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

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

    add_page = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "add",
            "--project",
            "crm-web",
            "--type",
            "page",
            "--slug",
            "ops-overview",
            "--title",
            "Ops Overview",
        ],
    )
    assert add_page.exit_code == 0, add_page.output

    link_page = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "link",
            "--project",
            "crm-web",
            "--from",
            "persona:sales-rep",
            "--to",
            "page:ops-overview",
        ],
    )
    assert link_page.exit_code == 0, link_page.output

    approve_result = invoke_with_root(
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
    assert approve_result.exit_code == 1, approve_result.output
    assert "hard dependencies are not approved" in approve_result.output.lower()
    assert "persona:sales-rep" in approve_result.output
    assert "stale" in approve_result.output.lower()
