"""Compatibility facade for repository helpers."""

from __future__ import annotations

from .repository_artifacts import (
    RepositoryError,
    add_dependency,
    artifact_ref,
    assert_no_cycles,
    build_dependency_graph,
    create_version_for_artifact,
    ensure_project,
    get_artifact_by_ref,
    get_project,
    list_artifacts,
    parse_artifact_ref,
    upsert_artifact,
)
from .repository_reviews import record_provider_call_audit, record_review

__all__ = [
    "RepositoryError",
    "add_dependency",
    "artifact_ref",
    "assert_no_cycles",
    "build_dependency_graph",
    "create_version_for_artifact",
    "ensure_project",
    "get_artifact_by_ref",
    "get_project",
    "list_artifacts",
    "parse_artifact_ref",
    "record_provider_call_audit",
    "record_review",
    "upsert_artifact",
]
