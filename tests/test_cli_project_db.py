from __future__ import annotations

from pathlib import Path

import pytest

from frontend_project_analysis.workflow.briefs import split_brief_text
from tests.cli_support import bootstrap_project, invoke_with_root, prepare_brief_source

pytestmark = pytest.mark.smoke


def test_top_level_init_bootstrap(tmp_path: Path) -> None:
    brief_source = prepare_brief_source(tmp_path)

    init_result = invoke_with_root(
        tmp_path,
        ["init", "--project", "crm-web", "--name", "CRM Web", "--brief-file", str(brief_source)],
    )
    assert init_result.exit_code == 0, init_result.output
    assert (tmp_path / ".frontend-project-analysis" / "state.db").exists()
    brief_path = tmp_path / "analysis" / "brief.md"
    assert brief_path.exists()
    metadata, _ = split_brief_text(brief_path.read_text(encoding="utf-8"))
    assert metadata["brief_status"] == "confirmed"
    assert metadata["brief_confirmed_by_user"] is True
    assert (tmp_path / "analysis" / "personas" / "index.md").exists()
    assert not (tmp_path / "pyproject.toml").exists()
    assert not (tmp_path / "Makefile").exists()
    assert not (tmp_path / "alembic.ini").exists()
    assert not (tmp_path / "migrations").exists()
    assert not (tmp_path / "src").exists()


def test_project_init_artifact_and_dependency_flow(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    assert (tmp_path / "analysis" / "personas").is_dir()
    assert (tmp_path / "analysis" / "index.md").exists()
    assert (tmp_path / "analysis" / "personas" / "index.md").exists()
    assert (tmp_path / "analysis" / "story-maps" / "index.md").exists()
    assert (tmp_path / "analysis" / "pages" / "index.md").exists()
    assert (tmp_path / "analysis" / "features" / "index.md").exists()
    assert (tmp_path / "analysis" / "relations" / "index.md").exists()
    assert (tmp_path / "analysis" / "relations" / "persona-story-page-matrix.md").exists()
    assert (tmp_path / "analysis" / "relations" / "feature-coverage-matrix.md").exists()
    assert (tmp_path / "analysis" / "relations" / "gwt-feature-matrix.md").exists()
    assert (tmp_path / "analysis" / "relations" / "graph.html").exists()
    root_index_text = (tmp_path / "analysis" / "index.md").read_text(encoding="utf-8")
    graph_html_text = (tmp_path / "analysis" / "relations" / "graph.html").read_text(
        encoding="utf-8"
    )
    assert "./relations/index.md" in root_index_text
    assert "./relations/graph.html" in root_index_text
    assert "Relationship Graph Placeholder" in graph_html_text
    assert "export graph-html --project crm-web" in graph_html_text
    assert (tmp_path / ".frontend-project-analysis" / "state.db").exists()
    gitignore_text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".frontend-project-analysis/" in gitignore_text
    assert (
        "Registered persona:alpha-persona"
        in invoke_with_root(
            tmp_path,
            [
                "artifact",
                "add",
                "--project",
                "crm-web",
                "--type",
                "persona",
                "--slug",
                "alpha-persona",
                "--title",
                "Alpha Persona",
            ],
        ).output
    )


def test_project_init_keeps_gitignore_entry_idempotent(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    second_init = invoke_with_root(
        tmp_path,
        [
            "project",
            "init",
            "--project",
            "crm-web",
            "--name",
            "CRM Web",
            "--brief-file",
            str(prepare_brief_source(tmp_path)),
        ],
    )
    assert second_init.exit_code == 0, second_init.output

    gitignore_lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert gitignore_lines.count(".frontend-project-analysis/") == 1


def test_project_init_force_reinitializes_database(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
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
            "ops-manager",
            "--title",
            "Ops Manager",
        ],
    )
    assert add_persona.exit_code == 0, add_persona.output

    force_init = invoke_with_root(
        tmp_path,
        [
            "project",
            "init",
            "--project",
            "crm-web",
            "--name",
            "CRM Web",
            "--brief-file",
            str(prepare_brief_source(tmp_path)),
            "--force",
        ],
    )
    assert force_init.exit_code == 0, force_init.output

    follow_up = invoke_with_root(
        tmp_path,
        [
            "artifact",
            "list",
            "--project",
            "crm-web",
        ],
    )
    assert follow_up.exit_code == 0, follow_up.output
    assert "ops-manager" not in follow_up.output


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
        [
            "project",
            "init",
            "--project",
            "crm-web",
            "--name",
            "CRM Web",
            "--brief-file",
            str(prepare_brief_source(tmp_path)),
        ],
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
            "alpha-persona",
            "--title",
            "Alpha Persona",
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
    assert "persona:alpha-persona" in gate_result.output
    assert "draft" in gate_result.output


def test_project_init_rejects_unconfirmed_brief(tmp_path: Path) -> None:
    brief_source = tmp_path / "draft-brief.md"
    brief_source.write_text(
        "# Project Brief\n\n"
        "## What does the product do?\n"
        "- Manage customer assignments.\n",
        encoding="utf-8",
    )

    result = invoke_with_root(
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

    assert result.exit_code != 0, result.output
    assert "Provide a confirmed brief" in result.output


def test_markdown_scan_refreshes_document_indexes(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    markdown_path = tmp_path / "analysis" / "pages" / "alpha-page.md"
    markdown_path.write_text(
        "---\n"
        "artifact_type: page\n"
        "slug: alpha-page\n"
        "round: 3\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Page\n"
        "---\n"
        "# Alpha Page\n"
        "\n"
        "## Accessible Persona\n"
        "- Alpha Persona\n"
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

    page_index = (tmp_path / "analysis" / "pages" / "index.md").read_text(encoding="utf-8")
    assert "Alpha Page" in page_index
    assert "/alpha-page" in page_index
    assert "[Alpha Page](./alpha-page.md)" in page_index


def test_markdown_scan_populates_feature_and_story_map_indexes(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    story_map_path = tmp_path / "analysis" / "story-maps" / "alpha-persona.md"
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

    feature_path = tmp_path / "analysis" / "features" / "alpha-feature.md"
    feature_path.write_text(
        "---\n"
        "artifact_type: feature\n"
        "slug: alpha-feature\n"
        "round: 4\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Feature\n"
        "---\n"
        "# Alpha Feature\n"
        "\n"
        "## Page\n"
        "- Alpha Page\n"
        "\n"
        "## Persona Served\n"
        "- Alpha Persona\n"
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

    story_map_index = (tmp_path / "analysis" / "story-maps" / "index.md").read_text(
        encoding="utf-8"
    )
    feature_index = (tmp_path / "analysis" / "features" / "index.md").read_text(encoding="utf-8")

    assert "Enter the customer workspace." in story_map_index
    assert "Leave the customer workspace." in story_map_index
    assert "[Alpha Persona](./alpha-persona.md)" in story_map_index
    assert "Alpha Persona Story Map" not in story_map_index
    assert "Lets sales reps reassign an account." in feature_index
    assert "Alpha Feature" in feature_index


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
            "alpha-persona",
            "--title",
            "Alpha Persona Story Map",
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
            "alpha-page",
            "--title",
            "Alpha Page",
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
            "story_map:alpha-persona",
            "--to",
            "persona:alpha-persona",
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
            "page:alpha-page",
            "--to",
            "story_map:alpha-persona",
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
            "feature:alpha-feature",
            "--to",
            "page:alpha-page",
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

    psp_path = tmp_path / "analysis" / "relations" / "persona-story-page-matrix.md"
    feature_path = tmp_path / "analysis" / "relations" / "feature-coverage-matrix.md"
    gwt_feature_path = tmp_path / "analysis" / "relations" / "gwt-feature-matrix.md"
    assert "story_map:alpha-persona" in psp_path.read_text(encoding="utf-8")
    assert "page:alpha-page" in psp_path.read_text(encoding="utf-8")
    assert "feature:alpha-feature" in feature_path.read_text(encoding="utf-8")
    assert "page:alpha-page" in feature_path.read_text(encoding="utf-8")
    assert "GWT Feature Matrix" in gwt_feature_path.read_text(encoding="utf-8")
    assert (
        "| Persona | Story Map | Page | Feature | GWT |"
        in psp_path.read_text(encoding="utf-8")
    )
    assert (
        "| Feature | Persona | Page | Story Map | GWT |"
        in feature_path.read_text(encoding="utf-8")
    )
    assert (
        "| GWT | Feature | Page | Persona | Story Map |"
        in gwt_feature_path.read_text(encoding="utf-8")
    )


def test_markdown_scan_reads_page_route_information_from_body(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    markdown_path = tmp_path / "analysis" / "pages" / "alpha-page.md"
    markdown_path.write_text(
        "---\n"
        "artifact_type: page\n"
        "slug: alpha-page\n"
        "round: 3\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Page\n"
        "---\n"
        "# Alpha Page\n"
        "\n"
        "## Route Information\n"
        "- Route: `/crm/alpha-page`\n"
        "\n"
        "## Accessible Persona\n"
        "- Alpha Persona\n"
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

    page_index = (tmp_path / "analysis" / "pages" / "index.md").read_text(encoding="utf-8")
    assert "/crm/alpha-page" in page_index
