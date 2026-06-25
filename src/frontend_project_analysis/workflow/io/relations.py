"""Relations matrix export helpers."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from ..state.definitions import WorkflowStateError
from .graph_export import build_graph_projection


def _graph_query_for_ref(ref: str, node: dict) -> str:
    if node["type"] == "persona":
        return urlencode({"persona": ref, "focus_ref": ref, "path_scope": "downstream"})
    if node["type"] == "feature":
        return urlencode({"feature": ref, "focus_ref": ref, "path_scope": "both"})
    if node["type"] == "gwt":
        return urlencode({"focus_ref": ref, "path_scope": "upstream"})
    return urlencode({"focus_ref": ref, "path_scope": "both"})


def _render_cell(ref: str, node_map: dict[str, dict]) -> str:
    if not ref:
        return ""
    node = node_map.get(ref)
    if node is None:
        raise WorkflowStateError(f"Relations row references unknown artifact '{ref}'.")
    graph_query = _graph_query_for_ref(ref, node)
    return f"[{ref}]({node['analysis_link']}) [↗](./graph.html?{graph_query})"


def _render_table(
    title: str,
    headers: tuple[str, ...],
    rows: list[dict],
    node_map: dict[str, dict],
    order: tuple[str, ...],
) -> str:
    lines = [
        title,
        "",
        f"| {' | '.join(headers)} |",
        f"| {' | '.join('---' for _ in headers)} |",
    ]
    for row in rows:
        values = [_render_cell(row[field_name], node_map) for field_name in order]
        lines.append(f"| {' | '.join(values)} |")
    return "\n".join(lines) + "\n"


def render_relations_markdown(session: Session, project, root: Path) -> list[Path]:
    payload = build_graph_projection(session, project, root)
    rows = payload["rows"]
    node_map = {node["ref"]: node for node in payload["nodes"]}

    relations_dir = root / "analysis" / "relations"
    relations_dir.mkdir(parents=True, exist_ok=True)

    psp_path = relations_dir / "persona-story-page-matrix.md"
    feature_path = relations_dir / "feature-coverage-matrix.md"
    gwt_feature_path = relations_dir / "gwt-feature-matrix.md"

    psp_path.write_text(
        _render_table(
            "# Persona Story Page Matrix",
            ("Persona", "Story Map", "Page", "Feature", "GWT"),
            rows,
            node_map,
            ("persona", "story_map", "page", "feature", "gwt"),
        ),
        encoding="utf-8",
    )
    feature_path.write_text(
        _render_table(
            "# Feature Coverage Matrix",
            ("Feature", "Persona", "Page", "Story Map", "GWT"),
            rows,
            node_map,
            ("feature", "persona", "page", "story_map", "gwt"),
        ),
        encoding="utf-8",
    )
    gwt_feature_path.write_text(
        _render_table(
            "# GWT Feature Matrix",
            ("GWT", "Feature", "Page", "Persona", "Story Map"),
            rows,
            node_map,
            ("gwt", "feature", "page", "persona", "story_map"),
        ),
        encoding="utf-8",
    )
    return [psp_path, feature_path, gwt_feature_path]
