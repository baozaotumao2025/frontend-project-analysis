from __future__ import annotations

from pathlib import Path

import pytest

from frontend_project_analysis.core.domain import ArtifactStatus, ArtifactType, DependencyType
from frontend_project_analysis.infrastructure.storage import session_scope
from frontend_project_analysis.repositories.dependencies import add_dependency, get_artifact_by_ref
from frontend_project_analysis.repositories.projects import ensure_project, get_project
from frontend_project_analysis.repositories.versions import upsert_artifact
from tests.cli_support import (
    bootstrap_project,
    invoke_with_root,
    prepare_database,
    prepare_feature_for_semantic_review,
)
from tests.workflow_support import approve_artifact

pytestmark = pytest.mark.smoke


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
