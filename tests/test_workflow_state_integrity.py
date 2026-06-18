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
