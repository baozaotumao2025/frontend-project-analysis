from __future__ import annotations

from pathlib import Path

import pytest

from tests.cli_support import (
    bootstrap_project,
    invoke_with_root,
    prepare_feature_for_semantic_review,
)

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
