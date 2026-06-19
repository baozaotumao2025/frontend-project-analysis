"""Markdown import helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from ...core.config import ANALYSIS_DIR_NAME, ensure_state_dirs
from ...core.domain import ArtifactStatus
from ...infrastructure.documents import infer_artifact_type, read_document
from ...models import Project
from ...repositories.versions import upsert_artifact
from .document_indexes import refresh_document_indexes
from .relations import render_relations_markdown


def _ensure_gitignore_entry(root: Path, entry: str) -> None:
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        existing_lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    else:
        existing_lines = []
    if any(line.strip() == entry for line in existing_lines):
        return
    existing_lines.append(entry)
    gitignore_path.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")


def initialize_project(
    paths,
    project_key: str,
    project_name: str,
    brief_text: str | None = None,
) -> dict[str, str]:
    ensure_state_dirs(paths)
    analysis_root = paths.root / ANALYSIS_DIR_NAME
    for relative in (
        "personas",
        "story-maps",
        "pages",
        "features",
        "relations",
        "gwt",
        "specs/features",
    ):
        (analysis_root / relative).mkdir(parents=True, exist_ok=True)
    analysis_root.mkdir(parents=True, exist_ok=True)
    if brief_text is not None:
        brief_path = analysis_root / "brief.md"
        brief_path.write_text(brief_text.rstrip() + "\n", encoding="utf-8")
    _ensure_gitignore_entry(paths.root, ".frontend-project-analysis/")
    refresh_document_indexes(paths.root)
    (analysis_root / "relations").mkdir(parents=True, exist_ok=True)
    for filename, title, headers in (
        (
            "persona-story-page-matrix.md",
            "# Persona Story Page Matrix",
            ("| Persona | Story Map | Page | Feature |\n| --- | --- | --- | --- |"),
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
        path = analysis_root / "relations" / filename
        path.write_text(f"{title}\n\n{headers}\n", encoding="utf-8")
    return {
        "project_key": project_key,
        "project_name": project_name,
        "state_dir": str(paths.state_dir),
        "analysis_dir": str(analysis_root),
    }


def import_markdown_files(
    session: Session,
    project: Project,
    root: Path,
    apply_changes: bool,
) -> list[dict]:
    candidates = [
        *sorted((root / ANALYSIS_DIR_NAME).rglob("*.md")),
        *sorted((root / ANALYSIS_DIR_NAME / "gwt").rglob("*.feature")),
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
