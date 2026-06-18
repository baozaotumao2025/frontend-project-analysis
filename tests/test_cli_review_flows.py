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
from frontend_project_analysis.schemas import ProviderAuditPayload, SemanticReviewPayload
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
    psp_path = tmp_path / "docs" / "relations" / "persona-story-page-matrix.md"
    feature_path = tmp_path / "docs" / "relations" / "feature-coverage-matrix.md"
    assert psp_path.exists()
    assert feature_path.exists()
    assert "Persona Story Page Matrix" in psp_path.read_text(encoding="utf-8")
    assert "Feature Coverage Matrix" in feature_path.read_text(encoding="utf-8")


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
