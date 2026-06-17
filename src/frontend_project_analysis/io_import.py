"""Import helpers for Markdown and manifests."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from .documents import infer_artifact_type, read_document
from .domain import ArtifactStatus, DependencyType
from .models import Project
from .repositories import add_dependency, parse_artifact_ref, upsert_artifact


def initialize_project(paths, project_key: str, project_name: str) -> dict[str, str]:
    from .config import ensure_state_dirs

    ensure_state_dirs(paths)
    for relative in (
        "docs/personas",
        "docs/story-maps",
        "docs/pages",
        "docs/features",
        "docs/relations",
        "docs/gwt",
        "specs/features",
    ):
        (paths.root / relative).mkdir(parents=True, exist_ok=True)
    return {
        "project_key": project_key,
        "project_name": project_name,
        "state_dir": str(paths.state_dir),
    }


def import_markdown_files(
    session: Session,
    project: Project,
    root: Path,
    apply_changes: bool,
) -> list[dict]:
    candidates = [
        *sorted((root / "docs").rglob("*.md")),
        *sorted((root / "specs").rglob("*.md")),
        *sorted((root / "docs" / "gwt").rglob("*.feature")),
    ]
    previews: list[dict] = []
    for path in candidates:
        inferred_type = infer_artifact_type(path)
        if inferred_type is None:
            continue
        metadata, _body = read_document(path)
        slug = str(metadata.get("slug") or path.stem.replace("-spec", ""))
        title = str(metadata.get("title") or path.stem.replace("-", " ").title())
        previews.append(
            {
                "path": str(path.relative_to(root)),
                "artifact_type": inferred_type.value,
                "slug": slug,
                "title": title,
            }
        )
        if apply_changes:
            upsert_artifact(
                session=session,
                project=project,
                artifact_type=inferred_type,
                slug=slug,
                title=title,
                source_path=str(path.relative_to(root)),
                status=ArtifactStatus(metadata.get("status", ArtifactStatus.DRAFT.value)),
                metadata=metadata,
                created_by="markdown-scan",
            )
    return previews


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
            status=ArtifactStatus(item["status"]),
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
