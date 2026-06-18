from __future__ import annotations

from pathlib import Path

import pytest

from tests.cli_support import bootstrap_project, invoke_with_root

pytestmark = pytest.mark.smoke


def test_project_init_artifact_and_dependency_flow(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    assert (tmp_path / "docs" / "personas").is_dir()
    assert (tmp_path / ".frontend-project-analysis" / "state.db").exists()
    assert "Registered persona:sales-rep" in invoke_with_root(
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
    ).output


def test_artifact_add_rejects_non_draft_status(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    result = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "add",
            "--project",
            "crm-web",
            "--type",
            "persona",
            "--slug",
            "ops-manager",
            "--title",
            "Ops Manager",
            "--status",
            "approved",
        ],
    )
    assert result.exit_code == 1, result.output
    assert "draft" in result.output.lower()


def test_database_backup_and_wipe(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    wipe_result = invoke_with_root(tmp_path, ["db", "wipe", "--yes"])
    assert wipe_result.exit_code == 0, wipe_result.output
    assert not (tmp_path / ".frontend-project-analysis" / "state.db").exists()

    init_result = invoke_with_root(tmp_path, ["db", "init"])
    assert init_result.exit_code == 0, init_result.output
    assert (tmp_path / ".frontend-project-analysis" / "state.db").exists()

    backup_result = invoke_with_root(tmp_path, ["db", "backup"])
    assert backup_result.exit_code == 0, backup_result.output
    backup_path = Path(backup_result.output.strip())
    assert backup_path.exists()
    assert backup_path.parent.name == "backups"


def test_database_wipe_then_reinitialize_supports_bootstrap_and_gate(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    wipe_result = invoke_with_root(tmp_path, ["db", "wipe", "--yes"])
    assert wipe_result.exit_code == 0, wipe_result.output
    assert not (tmp_path / ".frontend-project-analysis" / "state.db").exists()

    init_result = invoke_with_root(tmp_path, ["db", "init"])
    assert init_result.exit_code == 0, init_result.output
    assert (tmp_path / ".frontend-project-analysis" / "state.db").exists()

    project_init_result = invoke_with_root(
        tmp_path,
        ["project", "init", "--project", "crm-web", "--name", "CRM Web"],
    )
    assert project_init_result.exit_code == 0, project_init_result.output

    persona_add_result = invoke_with_root(
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
    assert persona_add_result.exit_code == 0, persona_add_result.output

    gate_result = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "2",
        ],
    )
    assert gate_result.exit_code == 1, gate_result.output
    assert "persona:sales-rep" in gate_result.output
    assert "draft" in gate_result.output
