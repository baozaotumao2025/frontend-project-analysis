from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from frontend_project_analysis.core.domain import ArtifactStatus, ArtifactType, DependencyType
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.repositories.dependencies import add_dependency, get_artifact_by_ref
from frontend_project_analysis.repositories.projects import ensure_project, get_project
from frontend_project_analysis.repositories.versions import upsert_artifact
from frontend_project_analysis.workflow.state.definitions import WorkflowStateError
from tests.cli_support import (
    bootstrap_project,
    invoke_with_root,
    prepare_database,
    prepare_feature_for_semantic_review,
)
from tests.workflow_support import approve_artifact

pytestmark = pytest.mark.smoke


@dataclass(frozen=True)
class RecoveryMatrixCase:
    round_number: int
    stale_source_ref: str
    blocked_ref: str
    wrong_recovery_ref: str
    correct_recovery_ref: str


RECOVERY_MATRIX: tuple[RecoveryMatrixCase, ...] = (
    RecoveryMatrixCase(
        round_number=4,
        stale_source_ref="page:customer-profile",
        blocked_ref="page:customer-profile",
        wrong_recovery_ref="feature:customer-assignment",
        correct_recovery_ref="page:customer-profile",
    ),
    RecoveryMatrixCase(
        round_number=5,
        stale_source_ref="page:customer-profile",
        blocked_ref="feature:customer-assignment",
        wrong_recovery_ref="gwt:customer-assignment",
        correct_recovery_ref="feature:customer-assignment",
    ),
    RecoveryMatrixCase(
        round_number=6,
        stale_source_ref="page:customer-profile",
        blocked_ref="gwt:customer-assignment",
        wrong_recovery_ref="feature_spec:customer-assignment",
        correct_recovery_ref="gwt:customer-assignment",
    ),
)


def _seed_full_chain(tmp_path: Path):
    paths = prepare_database(tmp_path)
    files = {
        "persona": tmp_path / "docs" / "personas" / "sales-rep.md",
        "story_map": tmp_path / "docs" / "story-maps" / "sales-assignment.md",
        "page": tmp_path / "docs" / "pages" / "customer-profile.md",
        "feature": tmp_path / "docs" / "features" / "customer-assignment.md",
        "gwt": tmp_path / "docs" / "gwt" / "customer-assignment.feature",
        "feature_spec": tmp_path / "specs" / "features" / "customer-assignment-spec.md",
    }
    for path in files.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{path.stem} v1", encoding="utf-8")

    with session_scope(paths) as session:
        project = ensure_project(session, "crm-web", "CRM Web", tmp_path)

        persona = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PERSONA,
            slug="sales-rep",
            title="Sales Rep",
            source_path=str(files["persona"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        approve_artifact(session, persona)

        story_map = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.STORY_MAP,
            slug="sales-assignment",
            title="Sales Assignment",
            source_path=str(files["story_map"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="story_map:sales-assignment",
            to_ref="persona:sales-rep",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )
        approve_artifact(session, story_map)

        page = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="customer-profile",
            title="Customer Profile",
            source_path=str(files["page"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="page:customer-profile",
            to_ref="story_map:sales-assignment",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )
        approve_artifact(session, page)

        feature = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(files["feature"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="feature:customer-assignment",
            to_ref="page:customer-profile",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )
        approve_artifact(session, feature)

        gwt = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.GWT,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(files["gwt"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="gwt:customer-assignment",
            to_ref="feature:customer-assignment",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )
        approve_artifact(session, gwt)

        feature_spec = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.FEATURE_SPEC,
            slug="customer-assignment",
            title="Customer Assignment",
            source_path=str(files["feature_spec"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="feature_spec:customer-assignment",
            to_ref="gwt:customer-assignment",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )
        approve_artifact(session, feature_spec)
        session.commit()

    return paths, files


@pytest.mark.parametrize("case", RECOVERY_MATRIX, ids=lambda case: f"round-{case.round_number}")
def test_workflow_start_reports_the_correct_blocking_ref_for_stale_chain(
    tmp_path: Path,
    case: RecoveryMatrixCase,
) -> None:
    paths, files = _seed_full_chain(tmp_path)

    stale_source_type = case.stale_source_ref.split(":", 1)[0]
    source_path = files[stale_source_type]
    source_path.write_text(f"{source_path.stem} v2", encoding="utf-8")
    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        artifact = upsert_artifact(
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
        assert artifact.status == ArtifactStatus.STALE
        session.commit()

    blocked_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            str(case.round_number),
        ],
    )
    assert blocked_gate.exit_code == 1, blocked_gate.output
    assert case.blocked_ref in blocked_gate.output
    assert "stale" in blocked_gate.output.lower()


@pytest.mark.parametrize("case", RECOVERY_MATRIX, ids=lambda case: f"round-{case.round_number}")
def test_workflow_start_stays_blocked_when_only_a_lower_downstream_layer_is_revalidated(
    tmp_path: Path,
    case: RecoveryMatrixCase,
) -> None:
    paths, files = _seed_full_chain(tmp_path)

    stale_source_type = case.stale_source_ref.split(":", 1)[0]
    source_path = files[stale_source_type]
    source_path.write_text(f"{source_path.stem} v2", encoding="utf-8")
    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = upsert_artifact(
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
        assert page.status == ArtifactStatus.STALE
        session.commit()

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        recovery_artifact = get_artifact_by_ref(session, project, case.wrong_recovery_ref)
        with pytest.raises(WorkflowStateError, match="hard dependencies are not approved"):
            approve_artifact(session, recovery_artifact)

    still_blocked_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            str(case.round_number),
        ],
    )
    assert still_blocked_gate.exit_code == 1, still_blocked_gate.output
    assert case.blocked_ref in still_blocked_gate.output
    assert "stale" in still_blocked_gate.output.lower()

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        correct_recovery = get_artifact_by_ref(session, project, case.correct_recovery_ref)
        if case.round_number == 4:
            approve_artifact(session, correct_recovery)
            session.commit()
        elif case.round_number == 5:
            with pytest.raises(WorkflowStateError, match="hard dependencies are not approved"):
                approve_artifact(session, correct_recovery)
            page = get_artifact_by_ref(session, project, "page:customer-profile")
            approve_artifact(session, page)
            approve_artifact(session, correct_recovery)
            session.commit()
        elif case.round_number == 6:
            with pytest.raises(WorkflowStateError, match="hard dependencies are not approved"):
                approve_artifact(session, correct_recovery)
            page = get_artifact_by_ref(session, project, "page:customer-profile")
            feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
            approve_artifact(session, page)
            approve_artifact(session, feature)
            approve_artifact(session, correct_recovery)
            feature_spec = get_artifact_by_ref(session, project, "feature_spec:customer-assignment")
            approve_artifact(session, feature_spec)
            session.commit()
        else:
            raise AssertionError(f"Unexpected round number: {case.round_number}")

    restored_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            str(case.round_number),
        ],
    )
    assert restored_gate.exit_code == 0, restored_gate.output


def test_workflow_gate_blocks_round_2_until_persona_is_approved(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)

    blocked_result = invoke_with_root(
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
    assert blocked_result.exit_code == 1, blocked_result.output
    assert "persona:sales-rep" in blocked_result.output
    assert "draft" in blocked_result.output

    prepare_feature_for_semantic_review(tmp_path)

    passed_result = invoke_with_root(
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
    assert passed_result.exit_code == 0, passed_result.output


def test_workflow_gate_blocks_round_3_when_story_maps_are_missing(tmp_path: Path) -> None:
    bootstrap_project(tmp_path)
    prepare_feature_for_semantic_review(tmp_path)

    blocked_result = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "3",
        ],
    )
    assert blocked_result.exit_code == 1, blocked_result.output
    assert "story_map" in blocked_result.output
    assert "no" in blocked_result.output.lower()


def test_workflow_start_blocks_when_approved_story_map_becomes_stale(
    tmp_path: Path,
) -> None:
    paths = prepare_database(tmp_path)
    persona_path = tmp_path / "docs" / "personas" / "sales-rep.md"
    story_map_path = tmp_path / "docs" / "story-maps" / "sales-assignment.md"
    persona_path.parent.mkdir(parents=True, exist_ok=True)
    story_map_path.parent.mkdir(parents=True, exist_ok=True)
    persona_path.write_text("Persona v1", encoding="utf-8")
    story_map_path.write_text("Story map v1", encoding="utf-8")

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
        approve_artifact(session, persona)

        story_map = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.STORY_MAP,
            slug="sales-assignment",
            title="Sales Assignment",
            source_path=str(story_map_path.relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        add_dependency(
            session=session,
            project=project,
            from_ref="story_map:sales-assignment",
            to_ref="persona:sales-rep",
            dependency_type=DependencyType.REQUIRES,
            is_hard=True,
        )
        approve_artifact(session, story_map)
        session.commit()

    initial_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "3",
        ],
    )
    assert initial_gate.exit_code == 0, initial_gate.output

    persona_path.write_text("Persona v2", encoding="utf-8")
    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
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
        story_map = get_artifact_by_ref(session, project, "story_map:sales-assignment")
        assert persona.status == ArtifactStatus.STALE
        assert story_map.status == ArtifactStatus.STALE
        session.commit()

    blocked_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "3",
        ],
    )
    assert blocked_gate.exit_code == 1, blocked_gate.output
    assert "stale" in blocked_gate.output.lower()
    assert "story_map:sales-assignment" in blocked_gate.output

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        persona = get_artifact_by_ref(session, project, "persona:sales-rep")
        approve_artifact(session, persona)
        story_map = get_artifact_by_ref(session, project, "story_map:sales-assignment")
        assert story_map.status == ArtifactStatus.STALE
        approve_artifact(session, story_map)
        session.commit()

    restored_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "3",
        ],
    )
    assert restored_gate.exit_code == 0, restored_gate.output


def test_workflow_start_blocks_round_4_when_page_becomes_stale(tmp_path: Path) -> None:
    paths, files = _seed_full_chain(tmp_path)

    initial_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "4",
        ],
    )
    assert initial_gate.exit_code == 0, initial_gate.output

    files["page"].write_text("Page v2", encoding="utf-8")
    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="customer-profile",
            title="Customer Profile",
            source_path=str(files["page"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        assert page.status == ArtifactStatus.STALE
        assert feature.status == ArtifactStatus.STALE
        session.commit()

    blocked_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "4",
        ],
    )
    assert blocked_gate.exit_code == 1, blocked_gate.output
    assert "page:customer-profile" in blocked_gate.output
    assert "stale" in blocked_gate.output.lower()

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        with pytest.raises(WorkflowStateError, match="hard dependencies are not approved"):
            approve_artifact(session, feature)

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project, "page:customer-profile")
        approve_artifact(session, page)
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        approve_artifact(session, feature)
        session.commit()

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project, "page:customer-profile")
        approve_artifact(session, page)
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        approve_artifact(session, feature)
        session.commit()

    restored_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "4",
        ],
    )
    assert restored_gate.exit_code == 0, restored_gate.output


def test_workflow_start_blocks_round_5_when_feature_becomes_stale(tmp_path: Path) -> None:
    paths, files = _seed_full_chain(tmp_path)

    initial_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "5",
        ],
    )
    assert initial_gate.exit_code == 0, initial_gate.output

    files["page"].write_text("Page v2", encoding="utf-8")
    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="customer-profile",
            title="Customer Profile",
            source_path=str(files["page"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        assert page.status == ArtifactStatus.STALE
        assert feature.status == ArtifactStatus.STALE
        session.commit()

    blocked_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "5",
        ],
    )
    assert blocked_gate.exit_code == 1, blocked_gate.output
    assert "feature:customer-assignment" in blocked_gate.output
    assert "stale" in blocked_gate.output.lower()

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        gwt = get_artifact_by_ref(session, project, "gwt:customer-assignment")
        with pytest.raises(WorkflowStateError, match="hard dependencies are not approved"):
            approve_artifact(session, gwt)

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project, "page:customer-profile")
        approve_artifact(session, page)
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        approve_artifact(session, feature)
        session.commit()

    restored_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "5",
        ],
    )
    assert restored_gate.exit_code == 0, restored_gate.output


def test_workflow_start_blocks_round_6_when_feature_spec_becomes_stale(
    tmp_path: Path,
) -> None:
    paths, files = _seed_full_chain(tmp_path)

    initial_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "6",
        ],
    )
    assert initial_gate.exit_code == 0, initial_gate.output

    files["page"].write_text("Page v2", encoding="utf-8")
    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="customer-profile",
            title="Customer Profile",
            source_path=str(files["page"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        feature_spec = get_artifact_by_ref(session, project, "feature_spec:customer-assignment")
        assert page.status == ArtifactStatus.STALE
        assert feature.status == ArtifactStatus.STALE
        assert (
            get_artifact_by_ref(session, project, "gwt:customer-assignment").status
            == ArtifactStatus.STALE
        )
        assert feature_spec.status == ArtifactStatus.STALE
        session.commit()

    blocked_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "6",
        ],
    )
    assert blocked_gate.exit_code == 1, blocked_gate.output
    assert "gwt:customer-assignment" in blocked_gate.output
    assert "stale" in blocked_gate.output.lower()

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project, "page:customer-profile")
        with pytest.raises(WorkflowStateError, match="hard dependencies are not approved"):
            approve_artifact(
                session, get_artifact_by_ref(session, project, "feature_spec:customer-assignment")
            )
        approve_artifact(session, page)
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        approve_artifact(session, feature)
        gwt = get_artifact_by_ref(session, project, "gwt:customer-assignment")
        approve_artifact(session, gwt)
        feature_spec = get_artifact_by_ref(session, project, "feature_spec:customer-assignment")
        approve_artifact(session, feature_spec)
        session.commit()

    restored_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "6",
        ],
    )
    assert restored_gate.exit_code == 0, restored_gate.output


def test_workflow_start_keeps_round_6_blocked_until_all_downstream_revalidated(
    tmp_path: Path,
) -> None:
    paths, files = _seed_full_chain(tmp_path)

    files["page"].write_text("Page v2", encoding="utf-8")
    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = upsert_artifact(
            session=session,
            project=project,
            artifact_type=ArtifactType.PAGE,
            slug="customer-profile",
            title="Customer Profile",
            source_path=str(files["page"].relative_to(tmp_path)),
            status=ArtifactStatus.DRAFT,
            metadata={},
            created_by="test",
        )
        feature = get_artifact_by_ref(session, project, "feature:customer-assignment")
        gwt = get_artifact_by_ref(session, project, "gwt:customer-assignment")
        feature_spec = get_artifact_by_ref(session, project, "feature_spec:customer-assignment")
        assert page.status == ArtifactStatus.STALE
        assert feature.status == ArtifactStatus.STALE
        assert gwt.status == ArtifactStatus.STALE
        assert feature_spec.status == ArtifactStatus.STALE
        session.commit()

    with session_scope(paths) as session:
        project = get_project(session, "crm-web")
        page = get_artifact_by_ref(session, project, "page:customer-profile")
        approve_artifact(session, page)
        session.commit()

    still_blocked_gate = invoke_with_root(
        tmp_path,
        [
            "workflow",
            "start",
            "--project",
            "crm-web",
            "--round",
            "6",
        ],
    )
    assert still_blocked_gate.exit_code == 1, still_blocked_gate.output
    assert "gwt:customer-assignment" in still_blocked_gate.output
    assert "stale" in still_blocked_gate.output.lower()
