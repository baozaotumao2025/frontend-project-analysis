from __future__ import annotations

from pathlib import Path

import pytest

from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.repositories.artifacts import list_artifacts
from frontend_project_analysis.repositories.projects import get_project
from tests.cli_support import project_paths
from tests.e2e_support import (
    PROJECT_KEY,
    PROJECT_NAME,
    assert_round_gate,
    create_existing_project_root,
    run_fpa,
    run_review_cycle,
    write_review_payload,
    write_round_artifacts,
)


@pytest.mark.e2e
@pytest.mark.e2e_install
def test_e2e_install_init_and_round_recovery(tmp_path: Path) -> None:
    root = create_existing_project_root(tmp_path)
    review_payload = write_review_payload(root)

    dry_run = run_fpa(root, ["install", "--dry-run"])
    assert dry_run.exit_code == 0, dry_run.output
    assert not (root / "alembic.ini").exists()

    install_result = run_fpa(root, ["install"])
    assert install_result.exit_code == 0, install_result.output
    assert "README.md" in install_result.output
    assert "skipped_existing" in install_result.output
    assert (root / "alembic.ini").exists()
    assert (root / "migrations" / "env.py").exists()
    assert (root / "src" / "frontend_project_analysis" / "cli.py").exists()

    init_result = run_fpa(root, ["init", "--project", PROJECT_KEY, "--name", PROJECT_NAME])
    assert init_result.exit_code == 0, init_result.output
    assert (root / ".frontend-project-analysis" / "state.db").exists()
    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    assert gitignore.count(".frontend-project-analysis/") == 1

    write_round_artifacts(
        root,
        story_map_complete=False,
        feature_spec_complete=False,
    )

    scan_result = run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    run_review_cycle(root, "persona:sales-rep", review_payload)
    assert_round_gate(root, 2, should_pass=True)

    blocked_round_3 = run_fpa(
        root,
        [
            "workflow",
            "start",
            "--project",
            PROJECT_KEY,
            "--round",
            "3",
        ],
    )
    assert blocked_round_3.exit_code != 0, blocked_round_3.output
    assert "story_map:sales-rep" in blocked_round_3.output
    assert "draft" in blocked_round_3.output

    story_map_failure = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "story_map:sales-rep",
        ],
    )
    assert story_map_failure.exit_code != 0, story_map_failure.output
    assert "missing_story_map_sections" in story_map_failure.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        feature_spec_complete=False,
    )
    scan_result = run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    run_review_cycle(root, "story_map:sales-rep", review_payload)
    assert_round_gate(root, 3, should_pass=True)

    run_review_cycle(root, "page:customer-profile", review_payload)
    assert_round_gate(root, 4, should_pass=True)

    run_review_cycle(root, "feature:customer-assignment", review_payload)
    assert_round_gate(root, 5, should_pass=True)

    run_review_cycle(root, "gwt:customer-assignment", review_payload)

    spec_failure = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "feature_spec:customer-assignment",
        ],
    )
    assert spec_failure.exit_code != 0, spec_failure.output
    assert "missing_state_boundary_terms" in spec_failure.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        feature_spec_complete=True,
    )
    scan_result = run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    run_review_cycle(root, "feature_spec:customer-assignment", review_payload)
    assert_round_gate(root, 6, should_pass=True)

    final_gate = run_fpa(
        root,
        [
            "workflow",
            "gate",
            "--project",
            PROJECT_KEY,
            "--round",
            "6",
        ],
    )
    assert final_gate.exit_code == 0, final_gate.output

    with session_scope(project_paths(root)) as session:
        project = get_project(session, PROJECT_KEY)
        approved_refs = {
            f"{artifact.artifact_type.value}:{artifact.slug}"
            for artifact in list_artifacts(session, project)
        }
        assert approved_refs == {
            "persona:sales-rep",
            "story_map:sales-rep",
            "page:customer-profile",
            "feature:customer-assignment",
            "gwt:customer-assignment",
            "feature_spec:customer-assignment",
        }


@pytest.mark.e2e
@pytest.mark.e2e_flow
def test_e2e_full_flow_multiple_failure_recovery(tmp_path: Path) -> None:
    root = create_existing_project_root(tmp_path, name="fpa-e2e-full-flow")
    review_payload = write_review_payload(root, filename="full-flow-review.json")

    install_result = run_fpa(root, ["install"])
    assert install_result.exit_code == 0, install_result.output

    init_result = run_fpa(root, ["init", "--project", PROJECT_KEY, "--name", PROJECT_NAME])
    assert init_result.exit_code == 0, init_result.output

    write_round_artifacts(
        root,
        story_map_complete=False,
        page_complete=False,
        feature_complete=False,
        gwt_complete=False,
        feature_spec_complete=False,
    )
    scan_result = run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    round_2_blocked = run_fpa(
        root,
        [
            "workflow",
            "start",
            "--project",
            PROJECT_KEY,
            "--round",
            "2",
        ],
    )
    assert round_2_blocked.exit_code != 0, round_2_blocked.output
    assert "persona:sales-rep" in round_2_blocked.output
    assert "draft" in round_2_blocked.output

    run_review_cycle(root, "persona:sales-rep", review_payload)
    assert_round_gate(root, 2, should_pass=True)

    round_3_blocked = run_fpa(
        root,
        [
            "workflow",
            "start",
            "--project",
            PROJECT_KEY,
            "--round",
            "3",
        ],
    )
    assert round_3_blocked.exit_code != 0, round_3_blocked.output
    assert "story_map:sales-rep" in round_3_blocked.output

    story_map_failure = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "story_map:sales-rep",
        ],
    )
    assert story_map_failure.exit_code != 0, story_map_failure.output
    assert "missing_story_map_sections" in story_map_failure.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        page_complete=False,
        feature_complete=False,
        gwt_complete=False,
        feature_spec_complete=False,
    )
    run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    run_review_cycle(root, "story_map:sales-rep", review_payload)
    assert_round_gate(root, 3, should_pass=True)

    round_4_blocked = run_fpa(
        root,
        [
            "workflow",
            "start",
            "--project",
            PROJECT_KEY,
            "--round",
            "4",
        ],
    )
    assert round_4_blocked.exit_code != 0, round_4_blocked.output
    assert "page:customer-profile" in round_4_blocked.output

    page_failure = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "page:customer-profile",
        ],
    )
    assert page_failure.exit_code != 0, page_failure.output
    assert "missing_page_sections" in page_failure.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        page_complete=True,
        feature_complete=False,
        gwt_complete=False,
        feature_spec_complete=False,
    )
    run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    run_review_cycle(root, "page:customer-profile", review_payload)
    assert_round_gate(root, 4, should_pass=True)

    round_5_blocked = run_fpa(
        root,
        [
            "workflow",
            "start",
            "--project",
            PROJECT_KEY,
            "--round",
            "5",
        ],
    )
    assert round_5_blocked.exit_code != 0, round_5_blocked.output
    assert "feature:customer-assignment" in round_5_blocked.output

    feature_failure = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "feature:customer-assignment",
        ],
    )
    assert feature_failure.exit_code != 0, feature_failure.output
    assert "missing_feature_sections" in feature_failure.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        page_complete=True,
        feature_complete=True,
        gwt_complete=False,
        feature_spec_complete=False,
    )
    run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    run_review_cycle(root, "feature:customer-assignment", review_payload)
    assert_round_gate(root, 5, should_pass=True)

    round_6_blocked = run_fpa(
        root,
        [
            "workflow",
            "start",
            "--project",
            PROJECT_KEY,
            "--round",
            "6",
        ],
    )
    assert round_6_blocked.exit_code != 0, round_6_blocked.output
    assert "gwt:customer-assignment" in round_6_blocked.output

    gwt_failure = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "gwt:customer-assignment",
        ],
    )
    assert gwt_failure.exit_code != 0, gwt_failure.output
    assert "incomplete_gwt_scenarios" in gwt_failure.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        page_complete=True,
        feature_complete=True,
        gwt_complete=True,
        feature_spec_complete=False,
    )
    run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    run_review_cycle(root, "gwt:customer-assignment", review_payload)
    assert_round_gate(root, 6, should_pass=True)

    spec_failure = run_fpa(
        root,
        [
            "review",
            "structural",
            "--project",
            PROJECT_KEY,
            "--artifact",
            "feature_spec:customer-assignment",
        ],
    )
    assert spec_failure.exit_code != 0, spec_failure.output
    assert "missing_state_boundary_terms" in spec_failure.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        page_complete=True,
        feature_complete=True,
        gwt_complete=True,
        feature_spec_complete=True,
    )
    run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    run_review_cycle(root, "feature_spec:customer-assignment", review_payload)

    final_gate = run_fpa(
        root,
        [
            "workflow",
            "gate",
            "--project",
            PROJECT_KEY,
            "--round",
            "6",
        ],
    )
    assert final_gate.exit_code == 0, final_gate.output


@pytest.mark.e2e
@pytest.mark.e2e_reset
def test_e2e_force_init_resets_project_state(tmp_path: Path) -> None:
    root = create_existing_project_root(tmp_path, name="fpa-e2e-reset")
    review_payload = write_review_payload(root, filename="force-review.json")

    install_result = run_fpa(root, ["install"])
    assert install_result.exit_code == 0, install_result.output

    init_result = run_fpa(root, ["init", "--project", PROJECT_KEY, "--name", PROJECT_NAME])
    assert init_result.exit_code == 0, init_result.output

    write_round_artifacts(
        root,
        story_map_complete=True,
        feature_spec_complete=True,
    )
    scan_result = run_fpa(
        root,
        [
            "import",
            "markdown-scan",
            "--project",
            PROJECT_KEY,
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    run_review_cycle(root, "persona:sales-rep", review_payload)

    with session_scope(project_paths(root)) as session:
        project = get_project(session, PROJECT_KEY)
        artifacts = list_artifacts(session, project)
        assert any(
            artifact.artifact_type.value == "persona" and artifact.slug == "sales-rep"
            for artifact in artifacts
        )

    force_init = run_fpa(
        root,
        [
            "init",
            "--project",
            PROJECT_KEY,
            "--name",
            PROJECT_NAME,
            "--force",
        ],
    )
    assert force_init.exit_code == 0, force_init.output
    assert (root / ".frontend-project-analysis" / "state.db").exists()

    with session_scope(project_paths(root)) as session:
        project = get_project(session, PROJECT_KEY)
        assert list_artifacts(session, project) == []
    assert (root / ".gitignore").read_text(encoding="utf-8").count(
        ".frontend-project-analysis/"
    ) == 1
