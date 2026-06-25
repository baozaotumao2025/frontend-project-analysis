from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from frontend_project_analysis.core.domain import ArtifactStatus, ArtifactType, DependencyType
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.models import ArtifactTransition
from frontend_project_analysis.repositories.artifacts import ensure_project
from frontend_project_analysis.repositories.dependencies import add_dependency
from frontend_project_analysis.repositories.versions import upsert_artifact
from frontend_project_analysis.workflow.state.ready import get_ready_artifacts
from frontend_project_analysis.workflow.state.structural import run_structural_checks
from tests.cli_support import prepare_database
from tests.workflow_support import approve_artifact


@pytest.mark.parametrize(
    ("metadata_factory", "expected_code"),
    [
        (
            lambda: {
                "artifact_type": "feature",
                "slug": "alpha-persona",
                "round": 1,
                "status": "draft",
                "project": "crm-web",
            },
            "artifact_type_mismatch",
        ),
        (
            lambda: {
                "artifact_type": "persona",
                "slug": "other",
                "round": 1,
                "status": "draft",
                "project": "crm-web",
            },
            "slug_mismatch",
        ),
        (
            lambda: {
                "artifact_type": "persona",
                "slug": "alpha-persona",
                "round": 99,
                "status": "draft",
                "project": "crm-web",
            },
            "round_frontmatter_mismatch",
        ),
        (
            lambda: {
                "artifact_type": "persona",
                "slug": "alpha-persona",
                "round": 1,
                "status": "draft",
                "project": "other-web",
            },
            "project_mismatch",
        ),
        (
            lambda: {
                "artifact_type": "persona",
                "slug": "alpha-persona",
                "round": 1,
                "project": "crm-web",
            },
            "missing_frontmatter_fields",
        ),
    ],
)
def test_run_structural_checks_reports_frontmatter_corruption(
    tmp_path: Path,
    metadata_factory,
    expected_code: str,
) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "personas" / "alpha-persona.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = metadata_factory()
    frontmatter = "\n".join(f"{key}: {value}" for key, value in metadata.items())
    source_path.write_text(f"---\n{frontmatter}\n---\n# Alpha Persona\n", encoding="utf-8")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="alpha-persona",
            title="Alpha Persona",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="persona:alpha-persona")
        assert expected_code in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_source(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "personas" / "alpha-persona.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        (
            "---\nartifact_type: persona\nslug: alpha-persona\nround: 1\nstatus: draft\n"
            "project: crm-web\n---\n# Alpha Persona\n"
        ),
        encoding="utf-8",
    )
    source_path.unlink()

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="alpha-persona",
            title="Alpha Persona",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="persona:alpha-persona")
        assert "missing_source" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_story_map_boundaries(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "story-maps" / "alpha-persona.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "---\n"
        "artifact_type: story_map\n"
        "slug: alpha-persona\n"
        "round: 2\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Persona Story Map\n"
        "---\n"
        "# Alpha Persona Story Map\n"
        "\n"
        "## Start\n"
        "- Enter the workspace.\n"
        "\n"
        "## Activity 1: Review\n"
        "- Step 1: Open record\n"
        "  - Story: View customer details\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.STORY_MAP,
            slug="alpha-persona",
            title="Alpha Persona Story Map",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="story_map:alpha-persona")
        assert "missing_story_map_sections" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_page_sections(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "pages" / "alpha-page.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
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
        "- Alpha Persona\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="alpha-page",
            title="Alpha Page",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="page:alpha-page")
        assert "missing_page_sections" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_feature_sections(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "features" / "alpha-feature.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
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
        "- Alpha Page\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="feature:alpha-feature")
        assert "missing_feature_sections" in {finding.code for finding in findings}


def test_run_structural_checks_reports_unknown_cross_references(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    page_path = tmp_path / "docs" / "pages" / "alpha-page.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(
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
        "- Route: `/alpha-page`\n"
        "\n"
        "## Accessible Persona\n"
        "- Alpha Persona\n"
        "\n"
        "## Story Steps Covered\n"
        "- Review customer details\n"
        "\n"
        "## Related Features\n"
        "- Nonexistent Feature\n",
        encoding="utf-8",
    )

    feature_path = tmp_path / "docs" / "features" / "alpha-feature.md"
    feature_path.parent.mkdir(parents=True, exist_ok=True)
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
        "- Unknown Page\n"
        "\n"
        "## Persona Served\n"
        "- Unknown Persona\n"
        "\n"
        "## Business Responsibility\n"
        "Lets sales reps reassign an account.\n"
        "\n"
        "## State Type\n"
        "- both\n"
        "\n"
        "## Cross-Page Reuse\n"
        "- yes\n"
        "\n"
        "## Source Story\n"
        "- Review customer details\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="alpha-page",
            title="Alpha Page",
            source_path=str(page_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(feature_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        page_findings = run_structural_checks(session, project, target_ref="page:alpha-page")
        feature_findings = run_structural_checks(
            session, project, target_ref="feature:alpha-feature"
        )
        assert "unknown_feature_reference" in {finding.code for finding in page_findings}
        assert "unknown_page_reference" in {finding.code for finding in feature_findings}
        assert "unknown_persona_reference" in {finding.code for finding in feature_findings}


def test_run_structural_checks_accepts_localized_aliases_and_markdown_links(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)
    persona_path = tmp_path / "docs" / "personas" / "alpha-persona.md"
    persona_path.parent.mkdir(parents=True, exist_ok=True)
    persona_path.write_text(
        "---\n"
        "artifact_type: persona\n"
        "slug: alpha-persona\n"
        "round: 1\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Persona\n"
        "---\n"
        "# Alpha Persona\n",
        encoding="utf-8",
    )

    page_path = tmp_path / "docs" / "pages" / "alpha-page.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(
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
        "- Route: `/alpha-page`\n"
        "\n"
        "## Accessible Persona\n"
        "- 销售代表\n"
        "\n"
        "## Story Steps Covered\n"
        "- Review customer details\n"
        "\n"
        "## Page Responsibility\n"
        "Shows the customer profile.\n"
        "\n"
        "## Related Features\n"
        "- [客户分配](../features/alpha-feature.md)\n",
        encoding="utf-8",
    )

    feature_path = tmp_path / "docs" / "features" / "alpha-feature.md"
    feature_path.parent.mkdir(parents=True, exist_ok=True)
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
        "- [Alpha Page](../pages/alpha-page.md)\n"
        "\n"
        "## Persona Served\n"
        "- 销售代表\n"
        "\n"
        "## Business Responsibility\n"
        "Lets sales reps reassign an account.\n"
        "\n"
        "## State Type\n"
        "- both\n"
        "\n"
        "## Cross-Page Reuse\n"
        "- yes\n"
        "\n"
        "## Source Story\n"
        "- Review customer details\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="alpha-persona",
            title="Alpha Persona",
            source_path=str(persona_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={"aliases": ["销售代表"]},
            created_by="test",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="alpha-page",
            title="Alpha Page",
            source_path=str(page_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(feature_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        page_findings = run_structural_checks(session, project, target_ref="page:alpha-page")
        feature_findings = run_structural_checks(
            session, project, target_ref="feature:alpha-feature"
        )
        assert "unknown_persona_reference" not in {finding.code for finding in page_findings}
        assert "unknown_feature_reference" not in {finding.code for finding in page_findings}
        assert "unknown_page_reference" not in {finding.code for finding in feature_findings}
        assert "unknown_persona_reference" not in {finding.code for finding in feature_findings}


def test_run_structural_checks_reports_unknown_localized_references(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    page_path = tmp_path / "docs" / "pages" / "alpha-page.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(
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
        "- Route: `/alpha-page`\n"
        "\n"
        "## Accessible Persona\n"
        "- [未定义角色](../personas/unknown-role.md)\n"
        "\n"
        "## Story Steps Covered\n"
        "- Review customer details\n"
        "\n"
        "## Related Features\n"
        "- [不存在的功能](../features/unknown-feature.md)\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="alpha-page",
            title="Alpha Page",
            source_path=str(page_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="page:alpha-page")
        assert "unknown_persona_reference" in {finding.code for finding in findings}
        assert "unknown_feature_reference" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_gwt_scenarios(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    gwt_path = tmp_path / "docs" / "gwt" / "alpha-feature.feature"
    gwt_path.parent.mkdir(parents=True, exist_ok=True)
    gwt_path.write_text(
        "---\n"
        "artifact_type: gwt\n"
        "slug: alpha-feature\n"
        "round: 5\n"
        "status: draft\n"
        "project: crm-web\n"
        "feature: alpha-feature\n"
        "title: Alpha Feature\n"
        "---\n"
        "\n"
        "Feature: alpha-feature\n\n"
        "  Scenario: Happy Path\n"
        "    Given Alpha Persona is signed in\n"
        "    When they reassign a customer\n"
        "    Then the customer is assigned\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(gwt_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="gwt:alpha-feature")
        assert "missing_gwt_scenarios" in {finding.code for finding in findings}
        assert "missing_frontmatter_fields" not in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_accessibility_gwt_scenario(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    gwt_path = tmp_path / "docs" / "gwt" / "alpha-feature.feature"
    gwt_path.parent.mkdir(parents=True, exist_ok=True)
    gwt_path.write_text(
        "---\n"
        "artifact_type: gwt\n"
        "slug: alpha-feature\n"
        "round: 5\n"
        "status: draft\n"
        "project: crm-web\n"
        "feature: alpha-feature\n"
        "title: Alpha Feature\n"
        "---\n"
        "\n"
        "Feature: alpha-feature\n\n"
        "  Scenario: Happy Path\n"
        "    Given Alpha Persona is signed in\n"
        "    When they reassign a customer\n"
        "    Then the customer is assigned\n\n"
        "  Scenario: Permission Case\n"
        "    Given Alpha Persona lacks permission\n"
        "    When they try to reassign a customer\n"
        "    Then the action is blocked\n\n"
        "  Scenario: Error Case\n"
        "    Given the service is unavailable\n"
        "    When the Alpha Persona reassigns the customer\n"
        "    Then an error is shown\n\n"
        "  Scenario: Edge Case\n"
        "    Given the customer is already assigned\n"
        "    When the Alpha Persona reassigns the customer\n"
        "    Then the assignment remains consistent\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(gwt_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="gwt:alpha-feature")
        assert "missing_gwt_scenarios" in {finding.code for finding in findings}


def test_run_structural_checks_reports_incomplete_gwt_scenarios(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    gwt_path = tmp_path / "docs" / "gwt" / "alpha-feature.feature"
    gwt_path.parent.mkdir(parents=True, exist_ok=True)
    gwt_path.write_text(
        "---\n"
        "artifact_type: gwt\n"
        "slug: alpha-feature\n"
        "round: 5\n"
        "status: draft\n"
        "project: crm-web\n"
        "feature: alpha-feature\n"
        "title: Alpha Feature\n"
        "---\n"
        "\n"
        "Feature: alpha-feature\n\n"
        "  Scenario: Happy Path\n"
        "    Given Alpha Persona is signed in\n"
        "    Then the customer is assigned\n\n"
        "  Scenario: Permission Case\n"
        "    Given Alpha Persona lacks permission\n"
        "    When they try to reassign a customer\n"
        "    Then the action is blocked\n\n"
        "  Scenario: Error Case\n"
        "    Given the service is unavailable\n"
        "    When they reassign a customer\n"
        "    Then an error is shown\n\n"
        "  Scenario: Edge Case\n"
        "    Given the customer is already assigned\n"
        "    When they reassign the customer\n"
        "    Then the assignment is updated\n\n"
        "  Scenario: Accessibility Case\n"
        "    Given the customer assignment drawer is open\n"
        "    When the Alpha Persona navigates with a keyboard\n"
        "    Then the reassignment remains usable\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(gwt_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="gwt:alpha-feature")
        assert "incomplete_gwt_scenarios" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_gwt_feature_reference(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    gwt_path = tmp_path / "docs" / "gwt" / "alpha-feature.feature"
    gwt_path.parent.mkdir(parents=True, exist_ok=True)
    gwt_path.write_text(
        "---\n"
        "artifact_type: gwt\n"
        "slug: alpha-feature\n"
        "round: 5\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Alpha Feature\n"
        "---\n"
        "\n"
        "Feature: alpha-feature\n\n"
        "  Scenario: Happy Path\n"
        "    Given Alpha Persona is signed in\n"
        "    When they reassign a customer\n"
        "    Then the customer is assigned\n\n"
        "  Scenario: Permission Case\n"
        "    Given Alpha Persona lacks permission\n"
        "    When they try to reassign a customer\n"
        "    Then the action is blocked\n\n"
        "  Scenario: Error Case\n"
        "    Given the service is unavailable\n"
        "    When the Alpha Persona reassigns the customer\n"
        "    Then an error is shown\n\n"
        "  Scenario: Edge Case\n"
        "    Given the customer is already assigned\n"
        "    When the Alpha Persona reassigns the customer\n"
        "    Then the assignment remains consistent\n\n"
        "  Scenario: Accessibility Case\n"
        "    Given the customer assignment drawer is open\n"
        "    When the Alpha Persona navigates with a keyboard\n"
        "    Then the reassignment remains usable\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(gwt_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="gwt:alpha-feature")
        assert "missing_gwt_feature_reference" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_feature_spec_sections(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    spec_path = tmp_path / "specs" / "features" / "alpha-feature-spec.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "# Alpha Feature - Feature Spec\n"
        "\n"
        "## Basic Information\n"
        "\n"
        "## Discovery And Evidence\n"
        "\n"
        "## Risks And Assumptions\n"
        "\n"
        "## Roles And Permissions\n"
        "\n"
        "## Component Breakdown\n"
        "\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE_SPEC,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(spec_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(
            session, project, target_ref="feature_spec:alpha-feature"
        )
        assert "missing_feature_spec_sections" in {finding.code for finding in findings}
        assert "missing_frontmatter_fields" not in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_state_boundary_terms(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    spec_path = tmp_path / "specs" / "features" / "alpha-feature-spec.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "# Alpha Feature - Feature Spec\n"
        "\n"
        "## Basic Information\n"
        "\n"
        "## Discovery And Evidence\n"
        "\n"
        "## Risks And Assumptions\n"
        "\n"
        "## Roles And Permissions\n"
        "\n"
        "## Component Breakdown\n"
        "\n"
        "## State Boundary\n"
        "- Shared cache\n"
        "\n"
        "## Accessibility\n"
        "\n"
        "## Observability\n"
        "\n"
        "## Release And Compliance\n"
        "\n"
        "## Cross-Feature Dependencies\n"
        "\n"
        "## Given-When-Then Acceptance Spec\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE_SPEC,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=str(spec_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(
            session, project, target_ref="feature_spec:alpha-feature"
        )
        assert "missing_state_boundary_terms" in {finding.code for finding in findings}


def test_run_structural_checks_reports_unapproved_dependency(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="alpha-persona",
            title="Alpha Persona",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="feature:alpha-feature",
            to_ref="persona:alpha-persona",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )

        findings = run_structural_checks(session, project, target_ref="feature:alpha-feature")
        assert "unapproved_dependency" in {finding.code for finding in findings}


def test_get_ready_artifacts_is_read_only_and_filters_by_approved_dependencies(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        approved_persona = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="alpha-persona",
            title="Alpha Persona",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        ready_feature = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="alpha-feature",
            title="Alpha Feature",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="feature:alpha-feature",
            to_ref="persona:alpha-persona",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )

        approve_artifact(session, approved_persona)

        before_statuses = {
            artifact.id: artifact.status for artifact in (approved_persona, ready_feature)
        }
        before_transitions = list(session.scalars(select(ArtifactTransition)).all())

        ready = get_ready_artifacts(session, project)

        after_statuses = {
            artifact.id: artifact.status for artifact in (approved_persona, ready_feature)
        }
        after_transitions = list(session.scalars(select(ArtifactTransition)).all())

        assert ready == ["feature:alpha-feature"]
        assert before_statuses == after_statuses
        assert before_transitions == after_transitions
