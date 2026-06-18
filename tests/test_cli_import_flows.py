from __future__ import annotations

import json
from pathlib import Path

import pytest

from frontend_project_analysis.core.domain import ArtifactStatus
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.repositories.dependencies import get_artifact_by_ref
from frontend_project_analysis.repositories.projects import get_project
from tests.cli_support import (
    approve_feature,
    bootstrap_project,
    invoke_with_root,
    prepare_feature_for_semantic_review,
    project_paths,
)

pytestmark = pytest.mark.smoke


def test_import_manifest_apply_updates_state(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    payload_path = tmp_path / "manifest.json"
    payload_path.write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "ref": "page:customer-profile",
                        "title": "Customer Profile",
                        "status": "draft",
                        "source_path": "docs/pages/customer-profile.md",
                        "metadata": {"slug": "customer-profile"},
                        "dependencies": [
                            {
                                "to": "persona:sales-rep",
                                "type": "requires",
                                "is_hard": True,
                            }
                        ],
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    preview_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "manifest",
            "--project",
            "crm-web",
            "--input",
            str(payload_path),
        ],
    )
    assert preview_result.exit_code == 0, preview_result.output
    assert '"apply": false' in preview_result.output

    apply_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "manifest",
            "--project",
            "crm-web",
            "--input",
            str(payload_path),
            "--apply",
        ],
    )
    assert apply_result.exit_code == 0, apply_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project_row, "page:customer-profile")
        assert page.status == ArtifactStatus.DRAFT
        assert any(dep.to_artifact.slug == "sales-rep" for dep in page.outgoing_dependencies)


def test_import_manifest_ignores_inbound_status_override(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    payload_path = tmp_path / "manifest.json"
    payload_path.write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "ref": "page:customer-profile",
                        "title": "Customer Profile",
                        "status": "approved",
                        "source_path": "docs/pages/customer-profile.md",
                        "metadata": {"slug": "customer-profile"},
                    }
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    apply_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "manifest",
            "--project",
            "crm-web",
            "--input",
            str(payload_path),
            "--apply",
        ],
    )
    assert apply_result.exit_code == 0, apply_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project_row, "page:customer-profile")
        assert page.status == ArtifactStatus.DRAFT


def test_import_markdown_content_change_resets_to_draft(tmp_path: Path) -> None:
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
        "Profile content.\n",
        encoding="utf-8",
    )

    apply_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert apply_result.exit_code == 0, apply_result.output

    structural_result = invoke_with_root(
        tmp_path,
        [
            "review",
            "structural",
            "--project",
            "crm-web",
            "--artifact",
            "page:customer-profile",
        ],
    )
    assert structural_result.exit_code == 0, structural_result.output

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
        "Profile content updated.\n",
        encoding="utf-8",
    )

    update_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert update_result.exit_code == 0, update_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project_row, "page:customer-profile")
        assert page.status == ArtifactStatus.DRAFT


def test_import_markdown_scan_ignores_frontmatter_status_override(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    markdown_path = tmp_path / "docs" / "pages" / "customer-profile.md"
    markdown_path.write_text(
        "---\n"
        "artifact_type: page\n"
        "slug: customer-profile\n"
        "round: 3\n"
        "status: approved\n"
        "project: crm-web\n"
        "title: Customer Profile\n"
        "---\n"
        "# Customer Profile\n"
        "\n"
        "Profile content.\n",
        encoding="utf-8",
    )

    apply_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert apply_result.exit_code == 0, apply_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project_row, "page:customer-profile")
        assert page.status == ArtifactStatus.DRAFT


def test_hard_dependency_on_approved_artifact_stales_dependents(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)
    approve_feature(tmp_path)

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

    link_result = invoke_with_root(
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
    assert link_result.exit_code == 0, link_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        persona = get_artifact_by_ref(session, project_row, "persona:sales-rep")
        feature = get_artifact_by_ref(session, project_row, "feature:customer-assignment")
        assert persona.status == ArtifactStatus.STALE
        assert feature.status == ArtifactStatus.STALE


def test_import_markdown_scan_apply_updates_state(tmp_path: Path) -> None:
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
        "Profile content.\n",
        encoding="utf-8",
    )

    preview_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
        ],
    )
    assert preview_result.exit_code == 0, preview_result.output
    assert '"apply": false' in preview_result.output
    assert "customer-profile.md" in preview_result.output

    apply_result = invoke_with_root(
        tmp_path,
        [
            "import",
            "markdown-scan",
            "--project",
            "crm-web",
            "--apply",
        ],
    )
    assert apply_result.exit_code == 0, apply_result.output

    with session_scope(project_paths(tmp_path)) as session:
        project_row = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project_row, "page:customer-profile")
        assert page.source_path == "docs/pages/customer-profile.md"
        assert page.title == "Customer Profile"
