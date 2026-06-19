from __future__ import annotations

from pathlib import Path

import pytest

from tests.cli_support import bootstrap_project, invoke_with_root

pytestmark = pytest.mark.smoke


def test_project_init_artifact_and_dependency_flow(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    assert (tmp_path / "docs" / "personas").is_dir()
    assert (tmp_path / "docs" / "index.md").exists()
    assert (tmp_path / "docs" / "personas" / "index.md").exists()
    assert (tmp_path / "docs" / "story-maps" / "index.md").exists()
    assert (tmp_path / "docs" / "pages" / "index.md").exists()
    assert (tmp_path / "docs" / "features" / "index.md").exists()
    assert (tmp_path / "docs" / "relations" / "persona-story-page-matrix.md").exists()
    assert (tmp_path / "docs" / "relations" / "feature-coverage-matrix.md").exists()
    assert (tmp_path / ".frontend-project-analysis" / "state.db").exists()
    gitignore_text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".frontend-project-analysis/" in gitignore_text
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


def test_project_init_keeps_gitignore_entry_idempotent(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    second_init = invoke_with_root(
        tmp_path,
        ["project", "init", "--project", "crm-web", "--name", "CRM Web"],
    )
    assert second_init.exit_code == 0, second_init.output

    gitignore_lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert gitignore_lines.count(".frontend-project-analysis/") == 1


def test_artifact_add_no_longer_accepts_status_override(tmp_path: Path) -> None:
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
    assert result.exit_code == 2, result.output
    assert "No such option: --status" in result.output


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


def test_markdown_scan_refreshes_document_indexes(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    markdown_path = tmp_path / "docs" / "pages" / "customer-profile.md"
    markdown_path.write_text(
        "---\n"
        "artifact_type: page\n"
        "slug: customer-profile\n"
        "round: 3\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Customer Profile\n"
        "---\n"
        "# Customer Profile\n"
        "\n"
        "## Accessible Persona\n"
        "- Sales Rep\n"
        "\n"
        "## Responsibility\n"
        "Shows the customer profile.\n",
        encoding="utf-8",
    )

    scan_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    page_index = (tmp_path / "docs" / "pages" / "index.md").read_text(encoding="utf-8")
    assert "Customer Profile" in page_index
    assert "/customer-profile" in page_index
    assert "[Customer Profile](./customer-profile.md)" in page_index


def test_markdown_scan_populates_feature_and_story_map_indexes(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    story_map_path = tmp_path / "docs" / "story-maps" / "sales-rep.md"
    story_map_path.write_text(
        "## Start\n"
        "- Enter the customer workspace.\n"
        "\n"
        "## Activity 1: Review\n"
        "- Step 1: Open record\n"
        "  - Story: View customer details\n"
        "\n"
        "- Step 2: Update data\n"
        "  - Story: Update customer info\n"
        "\n"
        "## End\n"
        "- Leave the customer workspace.\n",
        encoding="utf-8",
    )

    feature_path = tmp_path / "docs" / "features" / "customer-assignment.md"
    feature_path.write_text(
        "---\n"
        "artifact_type: feature\n"
        "slug: customer-assignment\n"
        "round: 4\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Customer Assignment\n"
        "---\n"
        "# Customer Assignment\n"
        "\n"
        "## Page\n"
        "- Customer Profile\n"
        "\n"
        "## Persona Served\n"
        "- Sales Rep\n"
        "\n"
        "## Business Responsibility\n"
        "Lets sales reps reassign an account.\n"
        "\n"
        "## State Type\n"
        "- both\n"
        "\n"
        "## Cross-Page Reuse\n"
        "- yes\n",
        encoding="utf-8",
    )

    scan_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    story_map_index = (tmp_path / "docs" / "story-maps" / "index.md").read_text(encoding="utf-8")
    feature_index = (tmp_path / "docs" / "features" / "index.md").read_text(encoding="utf-8")

    assert "Enter the customer workspace." in story_map_index
    assert "Leave the customer workspace." in story_map_index
    assert "[Sales Rep](./sales-rep.md)" in story_map_index
    assert "Sales Rep Story Map" not in story_map_index
    assert "Lets sales reps reassign an account." in feature_index
    assert "Customer Assignment" in feature_index


def test_markdown_scan_apply_refreshes_relation_matrices(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    story_map_add = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "add",
            "--project",
            "crm-web",
            "--type",
            "story_map",
            "--slug",
            "sales-rep",
            "--title",
            "Sales Rep Story Map",
        ],
    )
    assert story_map_add.exit_code == 0, story_map_add.output

    page_add = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "add",
            "--project",
            "crm-web",
            "--type",
            "page",
            "--slug",
            "customer-profile",
            "--title",
            "Customer Profile",
        ],
    )
    assert page_add.exit_code == 0, page_add.output

    story_link = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "link",
            "--project",
            "crm-web",
            "--from",
            "story_map:sales-rep",
            "--to",
            "persona:sales-rep",
        ],
    )
    assert story_link.exit_code == 0, story_link.output

    page_link = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "link",
            "--project",
            "crm-web",
            "--from",
            "page:customer-profile",
            "--to",
            "story_map:sales-rep",
        ],
    )
    assert page_link.exit_code == 0, page_link.output

    feature_link = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "link",
            "--project",
            "crm-web",
            "--from",
            "feature:customer-assignment",
            "--to",
            "page:customer-profile",
        ],
    )
    assert feature_link.exit_code == 0, feature_link.output

    scan_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    psp_path = tmp_path / "docs" / "relations" / "persona-story-page-matrix.md"
    feature_path = tmp_path / "docs" / "relations" / "feature-coverage-matrix.md"
    assert "story_map:sales-rep" in psp_path.read_text(encoding="utf-8")
    assert "page:customer-profile" in psp_path.read_text(encoding="utf-8")
    assert "feature:customer-assignment" in feature_path.read_text(encoding="utf-8")
    assert "page:customer-profile" in feature_path.read_text(encoding="utf-8")


def test_markdown_scan_reads_page_route_information_from_body(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    markdown_path = tmp_path / "docs" / "pages" / "customer-profile.md"
    markdown_path.write_text(
        "---\n"
        "artifact_type: page\n"
        "slug: customer-profile\n"
        "round: 3\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Customer Profile\n"
        "---\n"
        "# Customer Profile\n"
        "\n"
        "## Route Information\n"
        "- Route: `/crm/customer-profile`\n"
        "\n"
        "## Accessible Persona\n"
        "- Sales Rep\n"
        "\n"
        "## Responsibility\n"
        "Shows the customer profile.\n",
        encoding="utf-8",
    )

    scan_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert scan_result.exit_code == 0, scan_result.output

    page_index = (tmp_path / "docs" / "pages" / "index.md").read_text(encoding="utf-8")
    assert "/crm/customer-profile" in page_index
