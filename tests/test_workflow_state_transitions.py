from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from frontend_project_analysis.core.domain import ArtifactStatus, ArtifactType
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.models import ArtifactTransition
from frontend_project_analysis.repositories.artifacts import ensure_project
from frontend_project_analysis.workflow import WorkflowStateError, assert_transition_allowed, transition_artifact
from frontend_project_analysis.repositories.versions import upsert_artifact
from tests.workflow_support import approve_artifact, artifact_in_status
from tests.cli_support import prepare_database


def test_assert_transition_allowed_rejects_invalid_jump() -> None:
    with pytest.raises(WorkflowStateError, match="Transition from 'draft' to 'approved'"):
        assert_transition_allowed(ArtifactStatus.DRAFT, ArtifactStatus.APPROVED)


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (ArtifactStatus.DRAFT, ArtifactStatus.STRUCTURALLY_VALID),
        (ArtifactStatus.STRUCTURALLY_VALID, ArtifactStatus.SEMANTIC_REVIEW),
        (ArtifactStatus.SEMANTIC_REVIEW, ArtifactStatus.APPROVED),
        (ArtifactStatus.APPROVED, ArtifactStatus.REJECTED),
        (ArtifactStatus.REJECTED, ArtifactStatus.DRAFT),
        (ArtifactStatus.STALE, ArtifactStatus.DRAFT),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.ARCHIVED),
    ],
)
def test_assert_transition_allowed_accepts_known_valid_edges(
    from_status: ArtifactStatus,
    to_status: ArtifactStatus,
) -> None:
    assert_transition_allowed(from_status, to_status)


@pytest.mark.parametrize(
    "status",
    [
        ArtifactStatus.SEMANTIC_REVIEW,
        ArtifactStatus.APPROVED,
        ArtifactStatus.REJECTED,
    ],
)
def test_assert_transition_allowed_accepts_explicit_self_transitions(
    status: ArtifactStatus,
) -> None:
    assert_transition_allowed(status, status)


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (ArtifactStatus.DRAFT, ArtifactStatus.APPROVED),
        (ArtifactStatus.STRUCTURALLY_VALID, ArtifactStatus.STALE),
        (ArtifactStatus.SEMANTIC_REVIEW, ArtifactStatus.STALE),
        (ArtifactStatus.APPROVED, ArtifactStatus.SEMANTIC_REVIEW),
        (ArtifactStatus.APPROVED, ArtifactStatus.DRAFT),
        (ArtifactStatus.REJECTED, ArtifactStatus.APPROVED),
        (ArtifactStatus.STALE, ArtifactStatus.APPROVED),
        (ArtifactStatus.STALE, ArtifactStatus.SEMANTIC_REVIEW),
        (ArtifactStatus.STALE, ArtifactStatus.ARCHIVED),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.DRAFT),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.APPROVED),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.REJECTED),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.SEMANTIC_REVIEW),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.STALE),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.SUPERSEDED),
        (ArtifactStatus.ARCHIVED, ArtifactStatus.DRAFT),
        (ArtifactStatus.ARCHIVED, ArtifactStatus.APPROVED),
        (ArtifactStatus.ARCHIVED, ArtifactStatus.REJECTED),
        (ArtifactStatus.ARCHIVED, ArtifactStatus.ARCHIVED),
    ],
)
def test_assert_transition_allowed_rejects_known_invalid_edges(
    from_status: ArtifactStatus,
    to_status: ArtifactStatus,
) -> None:
    with pytest.raises(WorkflowStateError):
        assert_transition_allowed(from_status, to_status)


def test_transition_artifact_requires_gate_sequence(tmp_path: Path) -> None:
    paths = prepare_database(tmp_path)

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        artifact = upsert_artifact(
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

        with pytest.raises(WorkflowStateError, match="Transition from 'draft' to 'approved'"):
            transition_artifact(
                session=session,
                artifact=artifact,
                to_status=ArtifactStatus.APPROVED,
                actor="test",
                reason="skip gate",
            )

        assert artifact.status == ArtifactStatus.DRAFT
        transition_rows = list(
            session.scalars(
                select(ArtifactTransition).where(ArtifactTransition.artifact_id == artifact.id)
            )
        )
        assert len(transition_rows) == 1


@pytest.mark.parametrize(
    ("initial_status", "next_status"),
    [
        (ArtifactStatus.REJECTED, ArtifactStatus.DRAFT),
        (ArtifactStatus.STALE, ArtifactStatus.STRUCTURALLY_VALID),
        (ArtifactStatus.STALE, ArtifactStatus.REJECTED),
        (ArtifactStatus.APPROVED, ArtifactStatus.REJECTED),
        (ArtifactStatus.APPROVED, ArtifactStatus.STALE),
        (ArtifactStatus.SUPERSEDED, ArtifactStatus.ARCHIVED),
    ],
)
def test_transition_artifact_supports_allowed_recovery_and_terminal_edges(
    tmp_path: Path,
    initial_status: ArtifactStatus,
    next_status: ArtifactStatus,
) -> None:
    paths = prepare_database(tmp_path)
    source_path = tmp_path / "docs" / "personas" / f"sales-rep-{initial_status.value}.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("first version", encoding="utf-8")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        artifact = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug=f"sales-rep-{initial_status.value}",
            title="Sales Rep",
            source_path=str(source_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )

        if initial_status == ArtifactStatus.REJECTED:
            artifact = transition_artifact(
                session=session,
                artifact=artifact,
                to_status=ArtifactStatus.REJECTED,
                actor="test",
                reason="reach rejected",
            )
        elif initial_status == ArtifactStatus.STALE:
            approve_artifact(session, artifact)
            source_path.write_text("second version", encoding="utf-8")
            artifact = upsert_artifact(
                session=session,
                project=project,
                artifact_type=ArtifactType.PERSONA,
                slug=f"sales-rep-{initial_status.value}",
                title="Sales Rep",
                source_path=str(source_path.relative_to(tmp_path)),
                status=ArtifactStatus.DRAFT,
                metadata={},
                created_by="test",
            )
        elif initial_status == ArtifactStatus.APPROVED:
            approve_artifact(session, artifact)
        elif initial_status == ArtifactStatus.SUPERSEDED:
            approve_artifact(session, artifact)
            artifact = transition_artifact(
                session=session,
                artifact=artifact,
                to_status=ArtifactStatus.SUPERSEDED,
                actor="test",
                reason="supersede revision",
            )
        else:
            raise AssertionError(f"Unsupported initial status: {initial_status}")

        artifact = transition_artifact(
            session=session,
            artifact=artifact,
            to_status=next_status,
            actor="test",
            reason=f"move to {next_status.value}",
        )
        assert artifact.status == next_status


@pytest.mark.parametrize(
    "target_status",
    [
        ArtifactStatus.SEMANTIC_REVIEW,
        ArtifactStatus.APPROVED,
        ArtifactStatus.REJECTED,
    ],
)
def test_transition_artifact_accepts_explicit_self_transitions(
    tmp_path: Path,
    target_status: ArtifactStatus,
) -> None:
    paths = prepare_database(tmp_path)

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        source_path = tmp_path / "docs" / "personas" / "sales-rep.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("first version", encoding="utf-8")
        artifact = artifact_in_status(
            session,
            project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            source_path=str(source_path.relative_to(tmp_path)),
            target_status=target_status,
        )

        transition_count_before = len(
            list(
                session.scalars(
                    select(ArtifactTransition).where(ArtifactTransition.artifact_id == artifact.id)
                )
            )
        )
        artifact = transition_artifact(
            session=session,
            artifact=artifact,
            to_status=target_status,
            actor="test",
            reason="record self transition",
        )
        transition_count_after = len(
            list(
                session.scalars(
                    select(ArtifactTransition).where(ArtifactTransition.artifact_id == artifact.id)
                )
            )
        )

        assert artifact.status == target_status
        assert transition_count_after == transition_count_before + 1


@pytest.mark.parametrize(
    "target_status",
    [
        ArtifactStatus.DRAFT,
        ArtifactStatus.STRUCTURALLY_VALID,
        ArtifactStatus.SEMANTIC_REVIEW,
        ArtifactStatus.APPROVED,
        ArtifactStatus.REJECTED,
        ArtifactStatus.STALE,
        ArtifactStatus.SUPERSEDED,
    ],
)
def test_superseded_rejects_reopen_attempts(
    tmp_path: Path,
    target_status: ArtifactStatus,
) -> None:
    paths = prepare_database(tmp_path)
    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        source_path = tmp_path / "docs" / "personas" / "sales-rep.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("first version", encoding="utf-8")
        artifact = artifact_in_status(
            session,
            project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            source_path=str(source_path.relative_to(tmp_path)),
            target_status=ArtifactStatus.SUPERSEDED,
        )

        with pytest.raises(WorkflowStateError):
            transition_artifact(
                session=session,
                artifact=artifact,
                to_status=target_status,
                actor="test",
                reason="attempt reopen",
            )


@pytest.mark.parametrize(
    "target_status",
    [
        ArtifactStatus.DRAFT,
        ArtifactStatus.STRUCTURALLY_VALID,
        ArtifactStatus.SEMANTIC_REVIEW,
        ArtifactStatus.APPROVED,
        ArtifactStatus.REJECTED,
        ArtifactStatus.STALE,
        ArtifactStatus.SUPERSEDED,
        ArtifactStatus.ARCHIVED,
    ],
)
def test_archived_rejects_all_reopen_attempts(
    tmp_path: Path,
    target_status: ArtifactStatus,
) -> None:
    paths = prepare_database(tmp_path)
    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)
        source_path = tmp_path / "docs" / "personas" / "sales-rep.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("first version", encoding="utf-8")
        artifact = artifact_in_status(
            session,
            project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            source_path=str(source_path.relative_to(tmp_path)),
            target_status=ArtifactStatus.ARCHIVED,
        )

        with pytest.raises(WorkflowStateError):
            transition_artifact(
                session=session,
                artifact=artifact,
                to_status=target_status,
                actor="test",
                reason="attempt reopen",
            )
