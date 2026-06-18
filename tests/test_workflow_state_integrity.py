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
                "slug": "sales-rep",
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
                "slug": "sales-rep",
                "round": 99,
                "status": "draft",
                "project": "crm-web",
            },
            "round_frontmatter_mismatch",
        ),
        (
            lambda: {
                "artifact_type": "persona",
                "slug": "sales-rep",
                "round": 1,
                "status": "draft",
                "project": "other-web",
            },
            "project_mismatch",
        ),
        (
            lambda: {
                "artifact_type": "persona",
                "slug": "sales-rep",
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
    source_path = tmp_path / "docs" / "personas" / "sales-rep.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = metadata_factory()
    frontmatter = "\n".join(f"{key}: {value}" for key, value in metadata.items())
    source_path.write_text(f"---\n{frontmatter}\n---\n# Sales Rep\n", encoding="utf-8")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="persona:sales-rep")
        assert expected_code in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_source(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "personas" / "sales-rep.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "---\nartifact_type: persona\nslug: sales-rep\nround: 1\nstatus: draft\nproject: crm-web\n---\n# Sales Rep\n",
        encoding="utf-8",
    )
    source_path.unlink()

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="persona:sales-rep")
        assert "missing_source" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_story_map_boundaries(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "story-maps" / "sales-rep.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "---\n"
        "artifact_type: story_map\n"
        "slug: sales-rep\n"
        "round: 2\n"
        "status: draft\n"
        "project: crm-web\n"
        "title: Sales Rep Story Map\n"
        "---\n"
        "# Sales Rep Story Map\n"
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
            slug="sales-rep",
            title="Sales Rep Story Map",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="story_map:sales-rep")
        assert "missing_story_map_sections" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_page_sections(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "pages" / "customer-profile.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
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
        "- Sales Rep\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="customer-profile",
            title="Customer Profile",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="page:customer-profile")
        assert "missing_page_sections" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_feature_sections(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "features" / "customer-assignment.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
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
        "- Customer Profile\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="feature:customer-assignment")
        assert "missing_feature_sections" in {finding.code for finding in findings}


def test_run_structural_checks_reports_unknown_cross_references(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    page_path = tmp_path / "docs" / "pages" / "customer-profile.md"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_text(
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
        "- Route: `/customer-profile`\n"
        "\n"
        "## Accessible Persona\n"
        "- Sales Rep\n"
        "\n"
        "## Story Steps Covered\n"
        "- Review customer details\n"
        "\n"
        "## Related Features\n"
        "- Nonexistent Feature\n",
        encoding="utf-8",
    )

    feature_path = tmp_path / "docs" / "features" / "customer-assignment.md"
    feature_path.parent.mkdir(parents=True, exist_ok=True)
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
            slug="customer-profile",
            title="Customer Profile",
            source_path=str(page_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(feature_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        page_findings = run_structural_checks(session, project, target_ref="page:customer-profile")
        feature_findings = run_structural_checks(session, project, target_ref="feature:customer-assignment")
        assert "unknown_feature_reference" in {finding.code for finding in page_findings}
        assert "unknown_page_reference" in {finding.code for finding in feature_findings}
        assert "unknown_persona_reference" in {finding.code for finding in feature_findings}


def test_run_structural_checks_reports_missing_gwt_scenarios(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    gwt_path = tmp_path / "docs" / "gwt" / "customer-assignment.feature"
    gwt_path.parent.mkdir(parents=True, exist_ok=True)
    gwt_path.write_text(
        "Feature: customer-assignment\n\n"
        "  Scenario: Happy Path\n"
        "    Given Sales Rep is signed in\n"
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
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(gwt_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="gwt:customer-assignment")
        assert "missing_gwt_scenarios" in {finding.code for finding in findings}
        assert "missing_frontmatter_fields" not in {finding.code for finding in findings}


def test_run_structural_checks_reports_incomplete_gwt_scenarios(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    gwt_path = tmp_path / "docs" / "gwt" / "customer-assignment.feature"
    gwt_path.parent.mkdir(parents=True, exist_ok=True)
    gwt_path.write_text(
        "Feature: customer-assignment\n\n"
        "  Scenario: Happy Path\n"
        "    Given Sales Rep is signed in\n"
        "    Then the customer is assigned\n\n"
        "  Scenario: Permission Case\n"
        "    Given Sales Rep lacks permission\n"
        "    When they try to reassign a customer\n"
        "    Then the action is blocked\n\n"
        "  Scenario: Error Case\n"
        "    Given the service is unavailable\n"
        "    When they reassign a customer\n"
        "    Then an error is shown\n\n"
        "  Scenario: Edge Case\n"
        "    Given the customer is already assigned\n"
        "    When they reassign the customer\n"
        "    Then the assignment is updated\n",
        encoding="utf-8",
    )

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(gwt_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="gwt:customer-assignment")
        assert "incomplete_gwt_scenarios" in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_feature_spec_sections(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    spec_path = tmp_path / "specs" / "features" / "customer-assignment-spec.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "# Customer Assignment - Feature Spec\n"
        "\n"
        "## Basic Information\n"
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
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(spec_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="feature_spec:customer-assignment")
        assert "missing_feature_spec_sections" in {finding.code for finding in findings}
        assert "missing_frontmatter_fields" not in {finding.code for finding in findings}


def test_run_structural_checks_reports_missing_state_boundary_terms(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)
    spec_path = tmp_path / "specs" / "features" / "customer-assignment-spec.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "# Customer Assignment - Feature Spec\n"
        "\n"
        "## Basic Information\n"
        "\n"
        "## Roles And Permissions\n"
        "\n"
        "## Component Breakdown\n"
        "\n"
        "## State Boundary\n"
        "- Shared cache\n"
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
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(spec_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        findings = run_structural_checks(session, project, target_ref="feature_spec:customer-assignment")
        assert "missing_state_boundary_terms" in {finding.code for finding in findings}


def test_run_structural_checks_reports_unapproved_dependency(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="feature:customer-assignment",
            to_ref="persona:sales-rep",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )

        findings = run_structural_checks(session, project, target_ref="feature:customer-assignment")
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
            slug="sales-rep",
            title="Sales Rep",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        ready_feature = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=None,
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="feature:customer-assignment",
            to_ref="persona:sales-rep",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )

        approve_artifact(session, approved_persona)

        before_statuses = {
            artifact.id: artifact.status
            for artifact in (approved_persona, ready_feature)
        }
        before_transitions = list(session.scalars(select(ArtifactTransition)).all())

        ready = get_ready_artifacts(session, project)

        after_statuses = {
            artifact.id: artifact.status
            for artifact in (approved_persona, ready_feature)
        }
        after_transitions = list(session.scalars(select(ArtifactTransition)).all())

        assert ready == ["feature:customer-assignment"]
        assert before_statuses == after_statuses
        assert before_transitions == after_transitions
