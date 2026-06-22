"""Manifest import helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ...core.domain import ArtifactStatus, DependencyType
from ...models import Project
from ...repositories.dependencies import add_dependency, parse_artifact_ref
from ...repositories.versions import upsert_artifact
from ..state.definitions import WorkflowStateError


def _validate_manifest_artifacts(artifact_items: list[dict]) -> None:
    seen_refs: dict[str, int] = {}
    for index, item in enumerate(artifact_items):
        if not isinstance(item, dict):
            raise WorkflowStateError(
                f"Manifest artifact entry at index {index} must be an object."
            )
        for field in ("ref", "title"):
            if field not in item:
                raise WorkflowStateError(
                    f"Manifest artifact entry at index {index} is missing '{field}'."
                )
        ref = str(item["ref"])
        previous_index = seen_refs.get(ref)
        if previous_index is not None:
            raise WorkflowStateError(
                f"Manifest contains duplicate artifact reference '{ref}' at indexes "
                f"{previous_index} and {index}."
            )
        seen_refs[ref] = index
        for dependency_index, dependency in enumerate(item.get("dependencies", [])):
            if not isinstance(dependency, dict):
                raise WorkflowStateError(
                    f"Dependency {dependency_index} for artifact '{ref}' must be an object."
                )
            for field in ("to", "type"):
                if field not in dependency:
                    raise WorkflowStateError(
                        f"Dependency {dependency_index} for artifact '{ref}' is missing "
                        f"'{field}'."
                    )


def import_manifest_payload(
    session: Session,
    project: Project,
    payload: dict,
    apply_changes: bool,
) -> dict:
    artifact_items = payload.get("artifacts", [])
    if not isinstance(artifact_items, list):
        raise WorkflowStateError("Manifest payload must contain an 'artifacts' array.")
    _validate_manifest_artifacts(artifact_items)
    preview: list[dict] = []
    for item in artifact_items:
        ref = item["ref"]
        artifact_type, slug = parse_artifact_ref(ref)
        preview.append(
            {
                "ref": ref,
                "title": item["title"],
                "status": item["status"],
                "dependency_count": len(item.get("dependencies", [])),
            }
        )
        if not apply_changes:
            continue
        upsert_artifact(
            session=session,
            project=project,
            artifact_type=artifact_type,
            slug=slug,
            title=item["title"],
            source_path=item.get("source_path"),
            status=ArtifactStatus.DRAFT,
            metadata=item.get("metadata", {}),
            created_by="manifest-import",
        )
    if apply_changes:
        for item in artifact_items:
            for dependency in item.get("dependencies", []):
                add_dependency(
                    session=session,
                    project=project,
                    from_ref=item["ref"],
                    to_ref=dependency["to"],
                    dependency_type=DependencyType(dependency["type"]),
                    is_hard=bool(dependency.get("is_hard", True)),
                )
    return {"apply": apply_changes, "artifacts": preview}
