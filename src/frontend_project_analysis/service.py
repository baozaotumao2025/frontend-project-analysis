"""Compatibility facade for workflow services."""

from __future__ import annotations

from .errors import AppError
from .workflow_io import (
    archive_provider_call,
    export_json_to_path,
    export_manifest,
    import_manifest_payload,
    import_markdown_files,
    initialize_project,
    render_relations_markdown,
)
from .workflow_state import (
    CheckFinding,
    build_semantic_packet,
    get_ready_artifacts,
    run_structural_checks,
    transition_artifact,
)
from .workflow_state import (
    WorkflowStateError as ServiceError,
)

__all__ = [
    "AppError",
    "CheckFinding",
    "ServiceError",
    "archive_provider_call",
    "build_semantic_packet",
    "export_json_to_path",
    "export_manifest",
    "get_ready_artifacts",
    "import_manifest_payload",
    "import_markdown_files",
    "initialize_project",
    "render_relations_markdown",
    "run_structural_checks",
    "transition_artifact",
]
