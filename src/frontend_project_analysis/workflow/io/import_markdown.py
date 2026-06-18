"""Markdown import helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from ...core.config import ensure_state_dirs
from ...core.domain import ArtifactStatus
from ...infrastructure.documents import infer_artifact_type, read_document
from ...models import Project
from ...repositories.versions import upsert_artifact
from .document_indexes import refresh_document_indexes
from .relations import render_relations_markdown


def initialize_project(paths, project_key: str, project_name: str) -> dict[str, str]:
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
    refresh_document_indexes(paths.root)
    (paths.root / "docs" / "relations").mkdir(parents=True, exist_ok=True)
    for filename, title, headers in (
        (
            "persona-story-page-matrix.md",
            "# Persona Story Page Matrix",
            (
                "| Persona | Story Map | Page | Feature |\n"
                "| --- | --- | --- | --- |"
            ),
        ),
        (
            "feature-coverage-matrix.md",
            "# Feature Coverage Matrix",
            (
                "| Feature | Service Persona | Source Page | Covered Story |\n"
                "| --- | --- | --- | --- |"
            ),
        ),
    ):
        path = paths.root / "docs" / "relations" / filename
        path.write_text(f"{title}\n\n{headers}\n", encoding="utf-8")
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
                status=ArtifactStatus.DRAFT,
                metadata=metadata,
                created_by="markdown-scan",
            )
    if apply_changes:
        refresh_document_indexes(root)
        render_relations_markdown(session, project, root)
    return previews
