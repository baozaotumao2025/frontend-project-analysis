"""Relations matrix export helpers."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from ...core.domain import ArtifactType
from ...repositories.dependencies import artifact_ref, list_artifacts


def render_relations_markdown(session: Session, project, root: Path) -> list[Path]:
    artifacts = list_artifacts(session, project)
    persona_story_page_lines = [
        "# Persona Story Page Matrix",
        "",
        "| From | Dependency | To | Hard |",
        "| --- | --- | --- | --- |",
    ]
    feature_coverage_lines = [
        "# Feature Coverage Matrix",
        "",
        "| Feature | Dependency | Related Artifact | Hard |",
        "| --- | --- | --- | --- |",
    ]
    for artifact in artifacts:
        ref = artifact_ref(artifact)
        for dependency in artifact.outgoing_dependencies:
            row = (
                f"| {ref} | {dependency.dependency_type.value} | "
                f"{artifact_ref(dependency.to_artifact)} | "
                f"{'yes' if dependency.is_hard else 'no'} |"
            )
            if artifact.artifact_type in {
                ArtifactType.PERSONA,
                ArtifactType.STORY_MAP,
                ArtifactType.PAGE,
            }:
                persona_story_page_lines.append(row)
            if artifact.artifact_type == ArtifactType.FEATURE:
                feature_coverage_lines.append(row)
    relations_dir = root / "docs" / "relations"
    relations_dir.mkdir(parents=True, exist_ok=True)
    psp_path = relations_dir / "persona-story-page-matrix.md"
    feature_path = relations_dir / "feature-coverage-matrix.md"
    psp_path.write_text("\n".join(persona_story_page_lines) + "\n", encoding="utf-8")
    feature_path.write_text("\n".join(feature_coverage_lines) + "\n", encoding="utf-8")
    return [psp_path, feature_path]

