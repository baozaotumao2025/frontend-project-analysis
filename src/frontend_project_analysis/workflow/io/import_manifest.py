"""Manifest import helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ...core.domain import ArtifactStatus, DependencyType
from ...models import Project
from ...repositories.dependencies import add_dependency, parse_artifact_ref
from ...repositories.versions import upsert_artifact


def import_manifest_payload(
    session: Session,
    project: Project,
    payload: dict,
    apply_changes: bool,
) -> dict:
    artifact_items = payload.get("artifacts", [])
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
