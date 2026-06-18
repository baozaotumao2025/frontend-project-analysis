"""Compatibility facade for workflow state helpers."""

from __future__ import annotations

from .packets import build_semantic_packet
from .state.definitions import CheckFinding, WorkflowStateError
from .state.gates import assert_artifact_status_in, assert_transition_allowed
from .state.ready import get_ready_artifacts
from .state.structural import run_structural_checks
from .state.transitions import mark_dependents_stale, transition_artifact

__all__ = [
    "CheckFinding",
    "assert_artifact_status_in",
    "assert_transition_allowed",
    "WorkflowStateError",
    "build_semantic_packet",
    "get_ready_artifacts",
    "mark_dependents_stale",
    "run_structural_checks",
    "transition_artifact",
]
