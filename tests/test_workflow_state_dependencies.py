from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from frontend_project_analysis.core.domain import ArtifactStatus, ArtifactType, DependencyType
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.models import ArtifactTransition
from frontend_project_analysis.repositories.artifacts import ensure_project
from frontend_project_analysis.repositories.dependencies import add_dependency
from frontend_project_analysis.repositories.errors import RepositoryError
from frontend_project_analysis.repositories.versions import upsert_artifact
from frontend_project_analysis.workflow import WorkflowStateError
from tests.cli_support import prepare_database
from tests.workflow_support import approve_artifact


def test_upsert_artifact_rejects_non_draft_creation(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)

        with pytest.raises(WorkflowStateError, match="Artifacts can only be created"):
            upsert_artifact(
                session=session,
                project=project,
                artifact_type=ArtifactType.PERSONA,
                slug="sales-rep",
                title="Sales Rep",
                source_path=None,
                status=ArtifactStatus.APPROVED,
                metadata={},
                created_by="test",
            )


def test_upsert_artifact_content_change_downgrades_approved_revision_to_stale(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)
    content_path = tmp_path / "docs" / "personas" / "sales-rep.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text("first version", encoding="utf-8")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        artifact = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=str(content_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        approve_artifact(session, artifact)

        content_path.write_text("second version", encoding="utf-8")
        artifact = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=str(content_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        assert artifact.status == ArtifactStatus.STALE
        transition_rows = list(
            session.scalars(
                select(ArtifactTransition)
                .where(ArtifactTransition.artifact_id == artifact.id)
                .order_by(ArtifactTransition.id)
            )
        )
        assert transition_rows[-1].to_status == ArtifactStatus.STALE.value


def test_add_dependency_stales_approved_source_and_approved_dependents(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        source = upsert_artifact(
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
        dependent = upsert_artifact(
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
        target = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="ops-overview",
            title="Ops Overview",
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
        approve_artifact(session, source)
        approve_artifact(session, dependent)

        add_dependency(
            session=session,
            project=project,
            from_ref="persona:sales-rep",
            to_ref="page:ops-overview",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )

        assert source.status == ArtifactStatus.STALE
        assert dependent.status == ArtifactStatus.STALE
        assert target.status == ArtifactStatus.DRAFT

        stale_transitions = list(
            session.scalars(
                select(ArtifactTransition)
                .where(ArtifactTransition.to_status == ArtifactStatus.STALE.value)
                .order_by(ArtifactTransition.id)
            )
        )
        assert any(t.artifact_id == source.id for t in stale_transitions)
        assert any(t.artifact_id == dependent.id for t in stale_transitions)


def test_upstream_content_change_cascades_stale_through_transitive_dependents(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)
    persona_path = tmp_path / "docs" / "personas" / "sales-rep.md"
    feature_path = tmp_path / "docs" / "features" / "customer-assignment.md"
    page_path = tmp_path / "docs" / "pages" / "customer-profile.md"
    for path, body in (
        (persona_path, "Persona v1"),
        (feature_path, "Feature v1"),
        (page_path, "Page v1"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        persona = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=str(persona_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        feature = upsert_artifact(
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
        page = upsert_artifact(
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
        add_dependency(
            session=session,
            project=project,
            from_ref="feature:customer-assignment",
            to_ref="persona:sales-rep",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="page:customer-profile",
            to_ref="feature:customer-assignment",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )

        approve_artifact(session, persona)
        approve_artifact(session, feature)
        approve_artifact(session, page)

        persona_path.write_text("Persona v2", encoding="utf-8")
        persona = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=str(persona_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        assert persona.status == ArtifactStatus.STALE
        assert feature.status == ArtifactStatus.STALE
        assert page.status == ArtifactStatus.STALE


def test_add_dependency_rejects_cycles(tmp_path: Path) -> None:
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

        with pytest.raises(RepositoryError, match="Dependency cycle detected"):
            add_dependency(
                session=session,
                project=project,
                from_ref="persona:sales-rep",
                to_ref="feature:customer-assignment",
                dependency_type=DependencyType.REQUIRES,
                is_hard=True,
            )
