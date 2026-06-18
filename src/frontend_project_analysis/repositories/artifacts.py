"""Compatibility facade for artifact repository helpers."""

from __future__ import annotations

from .dependencies import (
    add_dependency,
    artifact_ref,
    assert_no_cycles,
    build_dependency_graph,
    get_artifact_by_ref,
    list_artifacts,
    parse_artifact_ref,
)
from .errors import RepositoryError
from .projects import ensure_project, get_project
from .versions import create_version_for_artifact, upsert_artifact

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
    "upsert_artifact",
]
