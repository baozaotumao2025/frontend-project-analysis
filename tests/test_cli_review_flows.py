from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import select

from frontend_project_analysis.core.domain import ArtifactStatus, ReviewKind, ReviewStatus
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
from tests.e2e_support import (
    PROJECT_KEY,
    PROJECT_NAME,
    create_existing_project_root,
    prepare_brief_source,
    run_fpa,
    run_review_cycle,
    write_review_payload,
    write_round_artifacts,
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
            "feature:alpha-feature",
            "--output",
            str(packet_path),
        ],
    )
    assert packet_result.exit_code == 0, packet_result.output
    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["artifact"]["ref"] == "feature:alpha-feature"
    assert packet["llm"]["provider"] == "host"
    assert packet["llm"]["review_isolation"]["mode"] == "fresh_reviewer_subagent"
    assert packet["llm"]["review_isolation"]["fork_context"] is False
    assert packet["llm"]["review_isolation"]["required"] is True

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
    assert any(item["ref"] == "feature:alpha-feature" for item in manifest["artifacts"])

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
    gwt_feature_path = tmp_path / "analysis" / "relations" / "gwt-feature-matrix.md"
    assert psp_path.exists()
    assert feature_path.exists()
    assert gwt_feature_path.exists()
    assert "Persona Story Page Matrix" in psp_path.read_text(encoding="utf-8")
    assert "Feature Coverage Matrix" in feature_path.read_text(encoding="utf-8")
    assert "GWT Feature Matrix" in gwt_feature_path.read_text(encoding="utf-8")
    assert "| Persona | Story Map | Page | Feature | GWT |" in psp_path.read_text(
        encoding="utf-8"
    )
    assert "| Feature | Persona | Page | Story Map | GWT |" in feature_path.read_text(
        encoding="utf-8"
    )
    assert "| GWT | Feature | Page | Persona | Story Map |" in gwt_feature_path.read_text(
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
            "feature:alpha-feature",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        review = session.scalar(
            select(ArtifactReview).where(
                ArtifactReview.artifact_id == artifact_row.id,
                ArtifactReview.review_kind == ReviewKind.SEMANTIC,
            )
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
    packet_path = tmp_path / "semantic-packet.json"

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
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
            "feature:alpha-feature",
            "--output",
            str(packet_path),
        ],
    )
    assert run_result.exit_code == 0, run_result.output
    assert "fresh reviewer sub-agent context" in run_result.output
    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["llm"]["review_isolation"]["mode"] == "fresh_reviewer_subagent"
    assert packet["fresh_session_required"] is True
    assert packet["packet_only"] is True
    assert packet["frozen_packet"] is True
    assert packet["analysis_inventory"]
    assert packet["coverage_ledger"]

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        review_count_after = len(
            session.scalars(
                select(ArtifactReview).where(ArtifactReview.artifact_id == artifact_row.id)
            ).all()
        )
        assert artifact_row.status == ArtifactStatus.STRUCTURALLY_VALID
        assert review_count_after == review_count_before


def test_review_semantic_run_blocks_when_focus_source_is_missing(
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
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        artifact_row.source_path = "analysis/features/alpha-feature.md"
        session.commit()

    run_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-run",
            "--project",
            "crm-web",
            "--artifact",
            "feature:alpha-feature",
        ],
    )
    assert run_result.exit_code != 0, run_result.output
    assert "source file" in run_result.output.lower()


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
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")

    run_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-run",
            "--project",
            "crm-web",
            "--artifact",
            "feature:alpha-feature",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        review = session.scalar(
            select(ArtifactReview)
            .where(
                ArtifactReview.artifact_id == artifact_row.id,
                ArtifactReview.review_kind == ReviewKind.SEMANTIC,
            )
            .order_by(ArtifactReview.id.desc())
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
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    monkeypatch.setenv("FPA_SEMANTIC_REVIEW_AUTO_APPROVE", "true")

    run_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-run",
            "--project",
            "crm-web",
            "--artifact",
            "feature:alpha-feature",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        review = session.scalar(
            select(ArtifactReview)
            .where(
                ArtifactReview.artifact_id == artifact_row.id,
                ArtifactReview.review_kind == ReviewKind.SEMANTIC,
            )
            .order_by(ArtifactReview.id.desc())
        )
        assert artifact_row.status == ArtifactStatus.APPROVED
        assert review is not None


def test_review_approve_requires_recorded_semantic_review(
    tmp_path: Path,
) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

    approve_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "approve",
            "--project",
            "crm-web",
            "--artifact",
            "feature:alpha-feature",
        ],
    )
    assert approve_result.exit_code == 1, approve_result.output
    assert "Expected one of: semantic_review" in approve_result.output


def test_review_semantic_record_missing_evidence_is_downgraded(
    tmp_path: Path,
) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

    feature_review_path = tmp_path / "feature-semantic-review-missing-evidence.json"
    feature_review_path.write_text(
        json.dumps(
            {
                "decision": "passed",
                "summary": "Feature semantic review passed.",
                "reviewer_ref": "fresh-llm",
                "model": "fake-model",
                "counterexamples": [],
                "findings": [
                    {
                        "severity": "INFO",
                        "code": "feature_boundary",
                        "message": "The feature slice has a concrete boundary.",
                        "evidence": [],
                        "details": {},
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    record_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "semantic-record",
            "--project",
            "crm-web",
            "--artifact",
            "feature:alpha-feature",
            "--input",
            str(feature_review_path),
        ],
    )
    assert record_result.exit_code == 0, record_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        review = session.scalar(
            select(ArtifactReview)
            .where(
                ArtifactReview.artifact_id == artifact_row.id,
                ArtifactReview.review_kind == ReviewKind.SEMANTIC,
            )
            .order_by(ArtifactReview.id.desc())
        )
        assert artifact_row.status == ArtifactStatus.SEMANTIC_REVIEW
        assert review is not None
        assert review.review_status == ReviewStatus.NEEDS_REVISION


def test_review_resubmit_reconciles_stale_markdown_and_records_semantic_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = create_existing_project_root(tmp_path, name="fpa-resubmit-project")
    brief_source = prepare_brief_source(root)

    init_result = run_fpa(
        root,
        [
            "init",
            "--project",
            PROJECT_KEY,
            "--name",
            PROJECT_NAME,
            "--brief-file",
            str(brief_source),
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    write_round_artifacts(root)

    import_result = run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    assert import_result.exit_code == 0, import_result.output

    review_payload = write_review_payload(root, filename="resubmit-review.json")
    run_review_cycle(root, "persona:alpha-persona", review_payload)
    run_review_cycle(root, "story_map:alpha-persona", review_payload)
    run_review_cycle(root, "page:alpha-page", review_payload)
    run_review_cycle(root, "feature:alpha-feature", review_payload)

    feature_path = root / "analysis" / "features" / "alpha-feature.md"
    feature_text = feature_path.read_text(encoding="utf-8")
    feature_path.write_text(
        feature_text.replace(
            "Assign customers to the right owner.",
            "Assign customers to the right owner and keep the handoff visible.",
        ),
        encoding="utf-8",
    )

    from frontend_project_analysis.commands.review import resubmit as resubmit_module

    def fake_run_semantic_review(packet: dict, settings=None) -> ProviderResponse:
        return fake_semantic_review_response(
            packet,
            decision=ReviewStatus.PASSED,
            summary="Semantic review passed after resubmit.",
        )

    monkeypatch.setattr(resubmit_module, "run_semantic_review", fake_run_semantic_review)
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")

    resubmit_result = run_fpa(
        root,
        [
            "review",
            "resubmit",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "feature:alpha-feature",
        ],
    )
    assert resubmit_result.exit_code == 0, resubmit_result.output

    with session_scope(project_paths(root)) as session:
        project_row = get_project(session, PROJECT_KEY)
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        review = session.scalar(
            select(ArtifactReview)
            .where(
                ArtifactReview.artifact_id == artifact_row.id,
                ArtifactReview.review_kind == ReviewKind.SEMANTIC,
            )
            .order_by(ArtifactReview.id.desc())
        )
        assert artifact_row.status == ArtifactStatus.SEMANTIC_REVIEW
        assert review is not None
        assert review.review_status == ReviewStatus.PASSED


def test_review_resubmit_host_mode_writes_packet_without_recording_semantic_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)
    monkeypatch.setenv("FPA_LLM_PROVIDER", "host")

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        semantic_before = len(
            session.scalars(
                select(ArtifactReview).where(
                    ArtifactReview.artifact_id == artifact_row.id,
                    ArtifactReview.review_kind == ReviewKind.SEMANTIC,
                )
            ).all()
        )

    resubmit_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "resubmit",
            "--project",
            "crm-web",
            "--artifact",
            "feature:alpha-feature",
        ],
    )
    assert resubmit_result.exit_code == 0, resubmit_result.output
    assert "fresh reviewer sub-agent context" in resubmit_result.output

    packet_path = (
        tmp_path
        / ".frontend-project-analysis"
        / "exports"
        / "feature-alpha-feature-resubmit-semantic-packet.json"
    )
    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["llm"]["review_isolation"]["mode"] == "fresh_reviewer_subagent"
    assert packet["fresh_session_required"] is True
    assert packet["packet_only"] is True

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        artifact_row = get_artifact_by_ref(session, project_row, "feature:alpha-feature")
        semantic_after = len(
            session.scalars(
                select(ArtifactReview).where(
                    ArtifactReview.artifact_id == artifact_row.id,
                    ArtifactReview.review_kind == ReviewKind.SEMANTIC,
                )
            ).all()
        )
        assert artifact_row.status == ArtifactStatus.STRUCTURALLY_VALID
        assert semantic_after == semantic_before


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
                "counterexamples": [
                    "A feature review should still identify a plausible coupling risk."
                ],
                "findings": [
                    {
                        "severity": "INFO",
                        "code": "feature_boundary",
                        "message": "The feature slice has a concrete boundary.",
                        "evidence": ["alpha-feature"],
                        "details": {},
                    }
                ],
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
            "feature:alpha-feature",
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
            "beta-page",
            "--title",
            "Beta Page",
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
            "persona:alpha-persona",
            "--to",
            "page:beta-page",
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
            "feature:alpha-feature",
        ],
    )
    assert approve_result.exit_code == 1, approve_result.output
    assert "hard dependencies are not approved" in approve_result.output.lower()
    assert "persona:alpha-persona" in approve_result.output
    assert "stale" in approve_result.output.lower()


def test_release_llm_review_packet_includes_prompt_contract(tmp_path: Path) -> None:
    packet_path = tmp_path / "release-review.md"
    result = subprocess.run(
        [
            "./scripts/release-llm-review.sh",
            "--skip-preflight",
            "--output",
            str(packet_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    text = packet_path.read_text(encoding="utf-8")
    assert "## Packet Manifest" in text
    assert "## Reviewer Card" in text
    assert "## System Prompt" in text
    assert "## User Prompt" in text
    assert '"fresh_session_required": true' in text


def test_release_card_outputs_only_reviewer_card(tmp_path: Path) -> None:
    card_path = tmp_path / "release-card.md"
    result = subprocess.run(
        [
            "./scripts/release-card.sh",
            "--output",
            str(card_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    text = card_path.read_text(encoding="utf-8")
    assert text.startswith("# Release Reviewer Card")
    assert "## Packet Manifest" not in text
    assert "## System Prompt" not in text
    assert "## User Prompt" not in text
    assert "fresh reviewer session" in text
