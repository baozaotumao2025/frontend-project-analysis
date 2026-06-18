"""Relations matrix export helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from ...core.domain import ArtifactType
from ...repositories.dependencies import artifact_ref, list_artifacts


def _collect_lineage_rows(artifact) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []

    def walk(current, persona: str = "", story_map: str = "", page: str = "") -> None:
        current_ref = artifact_ref(current)
        if current.artifact_type == ArtifactType.PERSONA:
            persona = current_ref
        elif current.artifact_type == ArtifactType.STORY_MAP:
            story_map = current_ref
        elif current.artifact_type == ArtifactType.PAGE:
            page = current_ref

        hard_dependencies = [dep.to_artifact for dep in current.outgoing_dependencies if dep.is_hard]
        if not hard_dependencies:
            rows.append((persona, story_map, page))
            return

        for dependency in hard_dependencies:
            walk(dependency, persona=persona, story_map=story_map, page=page)

    walk(artifact)
    unique_rows: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        unique_rows.append(row)
    return unique_rows


def _render_relation_row(persona: str, story_map: str, page: str, feature: str) -> str:
    return f"| {persona} | {story_map} | {page} | {feature} |"


def render_relations_markdown(session: Session, project, root: Path) -> list[Path]:
    artifacts = list_artifacts(session, project)
    persona_story_page_lines = [
        "# Persona Story Page Matrix",
        "",
        "| Persona | Story Map | Page | Feature |",
        "| --- | --- | --- | --- |",
    ]
    feature_coverage_lines = [
        "# Feature Coverage Matrix",
        "",
        "| Feature | Service Persona | Source Page | Covered Story |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in artifacts:
        lineage_rows = _collect_lineage_rows(artifact)
        feature_ref = artifact_ref(artifact) if artifact.artifact_type == ArtifactType.FEATURE else ""
        for persona, story_map, page in lineage_rows:
            persona_story_page_lines.append(_render_relation_row(persona, story_map, page, feature_ref))
            if artifact.artifact_type == ArtifactType.FEATURE:
                feature_coverage_lines.append(
                    _render_relation_row(feature_ref, persona, page, story_map)
                )
    relations_dir = root / "docs" / "relations"
    relations_dir.mkdir(parents=True, exist_ok=True)
    psp_path = relations_dir / "persona-story-page-matrix.md"
    feature_path = relations_dir / "feature-coverage-matrix.md"
    psp_path.write_text("\n".join(persona_story_page_lines) + "\n", encoding="utf-8")
    feature_path.write_text("\n".join(feature_coverage_lines) + "\n", encoding="utf-8")
    return [psp_path, feature_path]
