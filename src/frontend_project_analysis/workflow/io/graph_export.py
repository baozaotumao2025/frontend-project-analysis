"""Graph export helpers built from the canonical artifact row set."""
# ruff: noqa: E501

from __future__ import annotations

import html
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from ...core.domain import ArtifactType
from ...repositories.dependencies import artifact_ref, list_artifacts
from ..state.definitions import WorkflowStateError

_ROW_ARTIFACT_TYPES = (
    ArtifactType.PERSONA,
    ArtifactType.STORY_MAP,
    ArtifactType.PAGE,
    ArtifactType.FEATURE,
    ArtifactType.GWT,
)
_ROW_FIELDS = ("persona", "story_map", "page", "feature", "gwt")
_TYPE_LABELS = {
    ArtifactType.PERSONA: "Persona",
    ArtifactType.STORY_MAP: "Story Map",
    ArtifactType.PAGE: "Page",
    ArtifactType.FEATURE: "Feature",
    ArtifactType.GWT: "GWT",
}
_TYPE_ORDER = {
    ArtifactType.PERSONA: 0,
    ArtifactType.STORY_MAP: 1,
    ArtifactType.PAGE: 2,
    ArtifactType.FEATURE: 3,
    ArtifactType.GWT: 4,
}
_TYPE_COLORS = {
    ArtifactType.PERSONA: "#135d66",
    ArtifactType.STORY_MAP: "#4f772d",
    ArtifactType.PAGE: "#b85c38",
    ArtifactType.FEATURE: "#8f2d56",
    ArtifactType.GWT: "#3d348b",
}
_LAYOUT_X_POSITIONS = {
    ArtifactType.PERSONA: 110,
    ArtifactType.STORY_MAP: 360,
    ArtifactType.PAGE: 610,
    ArtifactType.FEATURE: 860,
    ArtifactType.GWT: 1110,
}
_CARD_WIDTH = 180
_CARD_HEIGHT = 56
_TOP_PADDING = 90
_VERTICAL_GAP = 86


@dataclass(frozen=True)
class RelationRow:
    persona: str = ""
    story_map: str = ""
    page: str = ""
    feature: str = ""
    gwt: str = ""


def _dedupe_rows(rows: list[RelationRow]) -> list[RelationRow]:
    unique_rows: list[RelationRow] = []
    seen: set[RelationRow] = set()
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        unique_rows.append(row)
    return unique_rows


def _sorted_rows(rows: list[RelationRow]) -> list[RelationRow]:
    return sorted(
        rows,
        key=lambda row: (row.persona, row.story_map, row.page, row.feature, row.gwt),
    )


def _row_with_ref(row: RelationRow, artifact_type: ArtifactType, ref: str) -> RelationRow:
    if artifact_type == ArtifactType.PERSONA:
        return RelationRow(ref, row.story_map, row.page, row.feature, row.gwt)
    if artifact_type == ArtifactType.STORY_MAP:
        return RelationRow(row.persona, ref, row.page, row.feature, row.gwt)
    if artifact_type == ArtifactType.PAGE:
        return RelationRow(row.persona, row.story_map, ref, row.feature, row.gwt)
    if artifact_type == ArtifactType.FEATURE:
        return RelationRow(row.persona, row.story_map, row.page, ref, row.gwt)
    if artifact_type == ArtifactType.GWT:
        return RelationRow(row.persona, row.story_map, row.page, row.feature, ref)
    return row


def _collect_upstream_rows(artifact, allowed_types: set[ArtifactType]) -> list[RelationRow]:
    rows: list[RelationRow] = []

    def walk(current, row: RelationRow) -> None:
        current_ref = artifact_ref(current)
        if current.artifact_type in allowed_types:
            row = _row_with_ref(row, current.artifact_type, current_ref)

        hard_dependencies = [
            dependency.to_artifact
            for dependency in current.outgoing_dependencies
            if dependency.is_hard and dependency.to_artifact.artifact_type in allowed_types
        ]
        if not hard_dependencies:
            rows.append(row)
            return

        for dependency in hard_dependencies:
            walk(dependency, row)

    walk(artifact, RelationRow())
    return _dedupe_rows(rows)


def _normalize_feature_ref(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    return normalized if ":" in normalized else f"feature:{normalized}"


def _resolve_gwt_feature_ref(artifact) -> str:
    feature_value = str((artifact.metadata_json or {}).get("feature") or "").strip()
    if not feature_value:
        raise WorkflowStateError(
            f"GWT '{artifact_ref(artifact)}' is missing frontmatter field 'feature'."
        )
    return _normalize_feature_ref(feature_value)


def _validate_gwt_feature_binding(artifact, artifact_map: dict[str, object]) -> str:
    gwt_ref = artifact_ref(artifact)
    feature_ref = _resolve_gwt_feature_ref(artifact)
    target_feature = artifact_map.get(feature_ref)
    if target_feature is None or target_feature.artifact_type != ArtifactType.FEATURE:
        raise WorkflowStateError(
            f"GWT '{gwt_ref}' references missing Feature '{feature_ref}'."
        )

    hard_feature_refs = sorted(
        artifact_ref(dependency.to_artifact)
        for dependency in artifact.outgoing_dependencies
        if dependency.is_hard and dependency.to_artifact.artifact_type == ArtifactType.FEATURE
    )
    if len(hard_feature_refs) > 1:
        raise WorkflowStateError(
            f"GWT '{gwt_ref}' has multiple hard-linked Features: {', '.join(hard_feature_refs)}."
        )
    if hard_feature_refs and hard_feature_refs[0] != feature_ref:
        raise WorkflowStateError(
            f"GWT '{gwt_ref}' frontmatter feature '{feature_ref}' does not match hard dependency "
            f"'{hard_feature_refs[0]}'."
        )
    return feature_ref


def _build_feature_context_rows(feature) -> list[RelationRow]:
    context_rows = _collect_upstream_rows(
        feature,
        {ArtifactType.PERSONA, ArtifactType.STORY_MAP, ArtifactType.PAGE, ArtifactType.FEATURE},
    )
    if not context_rows:
        return [RelationRow(feature=artifact_ref(feature))]
    return [
        RelationRow(
            persona=row.persona,
            story_map=row.story_map,
            page=row.page,
            feature=artifact_ref(feature),
        )
        for row in context_rows
    ]


def _default_projection_path(artifact_type: ArtifactType, slug: str) -> str:
    if artifact_type == ArtifactType.PERSONA:
        return f"analysis/personas/{slug}.md"
    if artifact_type == ArtifactType.STORY_MAP:
        return f"analysis/story-maps/{slug}.md"
    if artifact_type == ArtifactType.PAGE:
        return f"analysis/pages/{slug}.md"
    if artifact_type == ArtifactType.FEATURE:
        return f"analysis/features/{slug}.md"
    if artifact_type == ArtifactType.GWT:
        return f"analysis/gwt/{slug}.feature"
    raise WorkflowStateError(
        f"Artifact type '{artifact_type.value}' does not have a default projection path."
    )


def _source_path_for_artifact(artifact) -> str:
    return artifact.source_path or _default_projection_path(artifact.artifact_type, artifact.slug)


def _project_link_path(target_path: Path, start_path: Path) -> str:
    return Path(os.path.relpath(target_path, start=start_path)).as_posix()


def _build_node_layouts(artifacts: list[object]) -> dict[str, dict[str, int]]:
    grouped: dict[ArtifactType, list[object]] = {artifact_type: [] for artifact_type in _ROW_ARTIFACT_TYPES}
    for artifact in artifacts:
        grouped[artifact.artifact_type].append(artifact)
    for group in grouped.values():
        group.sort(key=artifact_ref)

    layouts: dict[str, dict[str, int]] = {}
    for artifact_type in _ROW_ARTIFACT_TYPES:
        for index, artifact in enumerate(grouped[artifact_type]):
            layouts[artifact_ref(artifact)] = {
                "column": _TYPE_ORDER[artifact_type],
                "row": index,
                "x": _LAYOUT_X_POSITIONS[artifact_type],
                "y": _TOP_PADDING + index * _VERTICAL_GAP,
                "width": _CARD_WIDTH,
                "height": _CARD_HEIGHT,
            }
    return layouts


def _build_graph_neighbors(edges: list[dict]) -> dict[str, dict[str, set[str]]]:
    neighbors: dict[str, dict[str, set[str]]] = {}
    for edge in edges:
        neighbors.setdefault(
            edge["from"],
            {"direct_upstream_refs": set(), "direct_downstream_refs": set(), "adjacent_refs": set()},
        )
        neighbors.setdefault(
            edge["to"],
            {"direct_upstream_refs": set(), "direct_downstream_refs": set(), "adjacent_refs": set()},
        )
        neighbors[edge["from"]]["direct_upstream_refs"].add(edge["to"])
        neighbors[edge["to"]]["direct_downstream_refs"].add(edge["from"])
        neighbors[edge["from"]]["adjacent_refs"].add(edge["to"])
        neighbors[edge["to"]]["adjacent_refs"].add(edge["from"])
    return neighbors


def _collect_transitive_refs(
    seed_ref: str,
    neighbors: dict[str, dict[str, set[str]]],
    direction: str,
) -> list[str]:
    if seed_ref not in neighbors:
        return []
    key = "direct_upstream_refs" if direction == "upstream" else "direct_downstream_refs"
    visited: set[str] = set()
    queue = list(neighbors[seed_ref][key])
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        queue.extend(sorted(neighbors.get(current, {}).get(key, set()) - visited))
    return sorted(visited)


def _build_relation_rows(artifacts: list[object]) -> list[RelationRow]:
    artifact_map = {artifact_ref(item): item for item in artifacts}
    gwt_refs_by_feature: dict[str, list[str]] = {}

    for artifact in artifacts:
        if artifact.artifact_type != ArtifactType.GWT:
            continue
        feature_ref = _validate_gwt_feature_binding(artifact, artifact_map)
        gwt_refs_by_feature.setdefault(feature_ref, []).append(artifact_ref(artifact))

    rows: list[RelationRow] = []
    covered_refs: set[str] = set()

    for feature in sorted(
        (artifact for artifact in artifacts if artifact.artifact_type == ArtifactType.FEATURE),
        key=artifact_ref,
    ):
        feature_ref = artifact_ref(feature)
        feature_rows = _build_feature_context_rows(feature)
        gwt_refs = sorted(gwt_refs_by_feature.get(feature_ref, [])) or [""]
        for feature_row in feature_rows:
            covered_refs.update(
                ref
                for ref in (
                    feature_row.persona,
                    feature_row.story_map,
                    feature_row.page,
                    feature_row.feature,
                )
                if ref
            )
            for gwt_ref in gwt_refs:
                rows.append(
                    RelationRow(
                        persona=feature_row.persona,
                        story_map=feature_row.story_map,
                        page=feature_row.page,
                        feature=feature_ref,
                        gwt=gwt_ref,
                    )
                )
        covered_refs.add(feature_ref)
        covered_refs.update(gwt_ref for gwt_ref in gwt_refs if gwt_ref)

    for artifact_type in (ArtifactType.PERSONA, ArtifactType.STORY_MAP, ArtifactType.PAGE):
        for artifact in sorted(
            (item for item in artifacts if item.artifact_type == artifact_type),
            key=artifact_ref,
        ):
            ref = artifact_ref(artifact)
            if ref in covered_refs:
                continue
            partial_rows = _collect_upstream_rows(
                artifact,
                {ArtifactType.PERSONA, ArtifactType.STORY_MAP, ArtifactType.PAGE},
            )
            if not partial_rows:
                partial_rows = [_row_with_ref(RelationRow(), artifact_type, ref)]
            for partial_row in partial_rows:
                rows.append(_row_with_ref(partial_row, artifact_type, ref))
            covered_refs.add(ref)

    for artifact in sorted(
        (item for item in artifacts if item.artifact_type == ArtifactType.GWT),
        key=artifact_ref,
    ):
        ref = artifact_ref(artifact)
        if ref in covered_refs:
            continue
        feature_ref = _validate_gwt_feature_binding(artifact, artifact_map)
        feature = artifact_map[feature_ref]
        feature_rows = _build_feature_context_rows(feature)
        for feature_row in feature_rows:
            rows.append(
                RelationRow(
                    persona=feature_row.persona,
                    story_map=feature_row.story_map,
                    page=feature_row.page,
                    feature=feature_ref,
                    gwt=ref,
                )
            )
        covered_refs.add(ref)

    return _sorted_rows(_dedupe_rows(rows))


def _validate_relation_rows(rows: list[RelationRow], artifacts: list[object]) -> dict[str, dict[str, int]]:
    actual_refs_by_type = {
        artifact_type: {
            artifact_ref(artifact)
            for artifact in artifacts
            if artifact.artifact_type == artifact_type
        }
        for artifact_type in _ROW_ARTIFACT_TYPES
    }
    row_refs_by_type = {
        ArtifactType.PERSONA: {row.persona for row in rows if row.persona},
        ArtifactType.STORY_MAP: {row.story_map for row in rows if row.story_map},
        ArtifactType.PAGE: {row.page for row in rows if row.page},
        ArtifactType.FEATURE: {row.feature for row in rows if row.feature},
        ArtifactType.GWT: {row.gwt for row in rows if row.gwt},
    }

    errors: list[str] = []
    for artifact_type in _ROW_ARTIFACT_TYPES:
        missing = sorted(actual_refs_by_type[artifact_type] - row_refs_by_type[artifact_type])
        unexpected = sorted(row_refs_by_type[artifact_type] - actual_refs_by_type[artifact_type])
        if missing:
            errors.append(
                f"{artifact_type.value} missing from relation rows: {', '.join(missing)}"
            )
        if unexpected:
            errors.append(
                f"{artifact_type.value} unexpectedly present in relation rows: "
                f"{', '.join(unexpected)}"
            )

    if errors:
        raise WorkflowStateError("Relations completeness check failed. " + " ".join(errors))

    return {
        artifact_type.value: {
            "artifact_count": len(actual_refs_by_type[artifact_type]),
            "row_count": len(row_refs_by_type[artifact_type]),
        }
        for artifact_type in _ROW_ARTIFACT_TYPES
    }


def build_graph_projection(session: Session, project, root: Path) -> dict:
    artifacts = [
        artifact
        for artifact in list_artifacts(session, project)
        if artifact.artifact_type in _ROW_ARTIFACT_TYPES
    ]
    artifact_map = {artifact_ref(item): item for item in artifacts}
    rows = _build_relation_rows(artifacts)
    coverage_summary = _validate_relation_rows(rows, artifacts)
    node_layouts = _build_node_layouts(artifacts)

    edges = []
    seen_edges: set[tuple[str, str, str, bool]] = set()
    for artifact in sorted(artifacts, key=artifact_ref):
        from_ref = artifact_ref(artifact)
        for dependency in artifact.outgoing_dependencies:
            to_ref = artifact_ref(dependency.to_artifact)
            if to_ref not in artifact_map:
                continue
            edge_key = (
                from_ref,
                to_ref,
                dependency.dependency_type.value,
                dependency.is_hard,
            )
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            edges.append(
                {
                    "from": from_ref,
                    "to": to_ref,
                    "type": dependency.dependency_type.value,
                    "is_hard": dependency.is_hard,
                }
            )
    edges.sort(key=lambda edge: (edge["from"], edge["to"], edge["type"], edge["is_hard"]))
    neighbors = _build_graph_neighbors(edges)

    nodes = []
    for artifact in sorted(artifacts, key=artifact_ref):
        path_text = _source_path_for_artifact(artifact)
        ref = artifact_ref(artifact)
        node_neighbors = neighbors.get(
            ref,
            {"direct_upstream_refs": set(), "direct_downstream_refs": set(), "adjacent_refs": set()},
        )
        nodes.append(
            {
                "ref": ref,
                "type": artifact.artifact_type.value,
                "type_label": _TYPE_LABELS[artifact.artifact_type],
                "slug": artifact.slug,
                "title": artifact.title,
                "round": artifact.round,
                "status": artifact.status.value,
                "source_path": path_text,
                "analysis_link": _project_link_path(
                    root / path_text,
                    root / "analysis" / "relations",
                ),
                "adjacent_refs": sorted(node_neighbors["adjacent_refs"]),
                "direct_upstream_refs": sorted(node_neighbors["direct_upstream_refs"]),
                "direct_downstream_refs": sorted(node_neighbors["direct_downstream_refs"]),
                "upstream_refs": _collect_transitive_refs(ref, neighbors, "upstream"),
                "downstream_refs": _collect_transitive_refs(ref, neighbors, "downstream"),
                "group": {
                    "lane": artifact.artifact_type.value,
                    "lane_label": _TYPE_LABELS[artifact.artifact_type],
                    "column": _TYPE_ORDER[artifact.artifact_type],
                },
                "layout": node_layouts[ref],
            }
        )

    return {
        "project": {
            "key": project.key,
            "name": project.name,
            "root_path": project.root_path,
        },
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "row_count": len(rows),
            "coverage": coverage_summary,
            "layout": {
                "card_width": _CARD_WIDTH,
                "card_height": _CARD_HEIGHT,
                "top_padding": _TOP_PADDING,
                "vertical_gap": _VERTICAL_GAP,
                "lanes": {
                    artifact_type.value: {
                        "column": _TYPE_ORDER[artifact_type],
                        "x": _LAYOUT_X_POSITIONS[artifact_type],
                        "label": _TYPE_LABELS[artifact_type],
                    }
                    for artifact_type in _ROW_ARTIFACT_TYPES
                },
            },
        },
        "nodes": nodes,
        "edges": edges,
        "rows": [asdict(row) for row in rows],
    }


def _escape_html_text(value: str) -> str:
    return html.escape(value, quote=True)


def _escape_json_script(payload: dict) -> str:
    return (
        json.dumps(payload, indent=2, ensure_ascii=True)
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
    )


def render_graph_placeholder_html(project_key: str, project_name: str) -> str:
    escaped_key = _escape_html_text(project_key)
    escaped_name = _escape_html_text(project_name)
    command = _escape_html_text(f"uv run fpa export graph-html --project {project_key}")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_name} Relationship Graph</title>
  <style>
    :root {{
      --bg: #f7f3ea;
      --panel: #fffaf2;
      --ink: #1f2430;
      --muted: #5f6b7a;
      --line: #d8ccb8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(29, 111, 141, 0.12), transparent 26rem),
        linear-gradient(180deg, #fbf8f1 0%, var(--bg) 100%);
    }}
    main {{
      max-width: 760px;
      padding: 28px;
      border-radius: 24px;
      border: 1px solid rgba(216, 204, 184, 0.9);
      background: rgba(255, 250, 242, 0.94);
      box-shadow: 0 14px 40px rgba(53, 47, 39, 0.08);
    }}
    h1 {{ margin-top: 0; }}
    code {{
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 0.92rem;
    }}
    .muted {{ color: var(--muted); }}
  </style>
</head>
<body>
  <main>
    <p class="muted">Relationship Graph Placeholder</p>
    <h1>{escaped_name}</h1>
    <p>The interactive relationship graph is an explicit export surface.</p>
    <p>Run <code>{command}</code> to generate the latest graph from SQLite state.</p>
    <p class="muted">Project key: <code>{escaped_key}</code></p>
  </main>
</body>
</html>
"""


def render_graph_html(payload: dict) -> str:
    graph_data = _escape_json_script(payload)
    escaped_project_name = _escape_html_text(payload["project"]["name"])
    escaped_project_key = _escape_html_text(payload["project"]["key"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_project_name} Relationship Graph</title>
  <style>
    :root {{
      --bg: #f7f3ea;
      --panel: #fffaf2;
      --ink: #1f2430;
      --muted: #5f6b7a;
      --line: #d8ccb8;
      --accent: #1d6f8d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(29, 111, 141, 0.12), transparent 26rem),
        linear-gradient(180deg, #fbf8f1 0%, var(--bg) 100%);
    }}
    .shell {{
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr) 320px;
      min-height: 100vh;
      gap: 16px;
      padding: 16px;
    }}
    .panel {{
      background: rgba(255, 250, 242, 0.92);
      border: 1px solid rgba(216, 204, 184, 0.9);
      border-radius: 20px;
      box-shadow: 0 14px 40px rgba(53, 47, 39, 0.08);
      overflow: hidden;
    }}
    .panel-inner {{ padding: 18px; }}
    h1, h2, h3 {{ margin: 0 0 10px; font-weight: 700; }}
    h1 {{ font-size: 1.45rem; }}
    h2 {{ font-size: 1rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }}
    p, li, label, input, button, select {{ font-size: 0.95rem; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px;
      background: rgba(255, 255, 255, 0.7);
    }}
    .stat strong {{ display: block; font-size: 1.2rem; }}
    .filters {{
      display: grid;
      gap: 12px;
      margin-top: 18px;
    }}
    .filters label {{
      display: block;
      color: var(--muted);
      margin-bottom: 5px;
    }}
    input[type="search"], select {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 12px;
      background: #fff;
      color: var(--ink);
    }}
    .toggle {{
      display: flex;
      gap: 8px;
      align-items: center;
      color: var(--ink);
    }}
    .graph-wrap {{
      position: relative;
      min-height: 720px;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 18px 18px 0;
    }}
    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: rgba(255,255,255,0.7);
    }}
    .swatch {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      display: inline-block;
    }}
    svg {{
      width: 100%;
      height: 100%;
      min-height: 720px;
      display: block;
    }}
    .node-link {{ text-decoration: none; }}
    .node-card {{
      rx: 18;
      ry: 18;
      stroke-width: 1.5;
      fill: rgba(255,255,255,0.96);
    }}
    .node-label {{
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      font-size: 13px;
      fill: var(--ink);
      pointer-events: none;
    }}
    .node-type {{
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      fill: var(--muted);
      pointer-events: none;
    }}
    .edge {{
      fill: none;
      stroke: rgba(72, 82, 97, 0.22);
      stroke-width: 2;
    }}
    .edge.hard {{
      stroke: rgba(29, 111, 141, 0.55);
      stroke-width: 2.5;
    }}
    .edge.hidden, .node.hidden {{
      opacity: 0.08;
    }}
    .edge.path-active {{
      stroke: rgba(184, 92, 56, 0.78);
      stroke-width: 3.5;
      opacity: 1;
    }}
    .node.active .node-card {{
      stroke-width: 3;
      filter: drop-shadow(0 10px 14px rgba(29, 111, 141, 0.18));
    }}
    .node.path-active .node-card {{
      stroke-width: 3;
      stroke: #b85c38;
      filter: drop-shadow(0 10px 14px rgba(184, 92, 56, 0.16));
    }}
    .detail-list, .coverage-list {{
      list-style: none;
      padding: 0;
      margin: 12px 0 0;
      display: grid;
      gap: 8px;
    }}
    .detail-list li, .coverage-list li {{
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 10px 12px;
      background: rgba(255,255,255,0.68);
    }}
    .mono {{
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 0.83rem;
    }}
    .muted {{ color: var(--muted); }}
    .detail-link {{
      color: var(--accent);
      text-decoration: none;
    }}
    @media (max-width: 1180px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}
      .graph-wrap, svg {{
        min-height: 560px;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="panel">
      <div class="panel-inner">
        <h2>Project</h2>
        <h1>{escaped_project_name}</h1>
        <p class="muted mono">{escaped_project_key}</p>
        <div class="summary">
          <div class="stat"><span class="muted">Nodes</span><strong id="nodeCount"></strong></div>
          <div class="stat"><span class="muted">Edges</span><strong id="edgeCount"></strong></div>
          <div class="stat"><span class="muted">Rows</span><strong id="rowCount"></strong></div>
          <div class="stat"><span class="muted">Visible</span><strong id="visibleCount"></strong></div>
        </div>
        <div class="filters">
          <div>
            <label for="search">Search</label>
            <input id="search" type="search" placeholder="feature:alpha-feature">
          </div>
          <div>
            <label for="personaFocus">Persona Focus</label>
            <select id="personaFocus"></select>
          </div>
          <div>
            <label for="featureFocus">Feature Focus</label>
            <select id="featureFocus"></select>
          </div>
          <div>
            <label for="typeFilter">Artifact Type</label>
            <select id="typeFilter"></select>
          </div>
          <div>
            <label for="rowFilter">Row Focus</label>
            <select id="rowFilter"></select>
          </div>
          <div>
            <label for="pathScope">Path Scope</label>
            <select id="pathScope">
              <option value="both">Both directions</option>
              <option value="upstream">Upstream only</option>
              <option value="downstream">Downstream only</option>
            </select>
          </div>
          <label class="toggle">
            <input id="hardOnly" type="checkbox">
            <span>Show hard dependencies only</span>
          </label>
        </div>
        <h2 style="margin-top:20px;">Coverage</h2>
        <ul class="coverage-list" id="coverage"></ul>
      </div>
    </section>
    <section class="panel graph-wrap">
      <div class="legend" id="legend"></div>
      <svg id="graph" viewBox="0 0 1320 820" preserveAspectRatio="xMidYMin meet"></svg>
    </section>
    <aside class="panel">
      <div class="panel-inner">
        <h2>Detail</h2>
        <h1 id="detailTitle">Select a node</h1>
        <p class="muted mono" id="detailRef">Click a node card to inspect it.</p>
        <ul class="detail-list" id="detailList"></ul>
      </div>
    </aside>
  </div>
  <script id="graph-data" type="application/json">{graph_data}</script>
  <script>
    const payload = JSON.parse(document.getElementById("graph-data").textContent);
    const params = new URLSearchParams(window.location.search);
    const colors = {json.dumps({item.value: color for item, color in _TYPE_COLORS.items()}, ensure_ascii=True)};
    const typeLabels = {json.dumps({item.value: label for item, label in _TYPE_LABELS.items()}, ensure_ascii=True)};
    const nodes = payload.nodes;
    const edges = payload.edges;
    const rows = payload.rows;
    const nodeMap = new Map(nodes.map((node) => [node.ref, node]));
    const svg = document.getElementById("graph");
    const search = document.getElementById("search");
    const personaFocus = document.getElementById("personaFocus");
    const featureFocus = document.getElementById("featureFocus");
    const typeFilter = document.getElementById("typeFilter");
    const rowFilter = document.getElementById("rowFilter");
    const pathScope = document.getElementById("pathScope");
    const hardOnly = document.getElementById("hardOnly");
    const detailTitle = document.getElementById("detailTitle");
    const detailRef = document.getElementById("detailRef");
    const detailList = document.getElementById("detailList");
    const visibleCount = document.getElementById("visibleCount");

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    document.getElementById("nodeCount").textContent = String(payload.summary.node_count);
    document.getElementById("edgeCount").textContent = String(payload.summary.edge_count);
    document.getElementById("rowCount").textContent = String(payload.summary.row_count);

    const coverageEl = document.getElementById("coverage");
    for (const [artifactType, item] of Object.entries(payload.summary.coverage)) {{
      const li = document.createElement("li");
      li.innerHTML = `<strong>${{typeLabels[artifactType] || artifactType}}</strong><br><span class="muted">${{item.row_count}} row refs / ${{item.artifact_count}} artifacts</span>`;
      coverageEl.appendChild(li);
    }}

    typeFilter.innerHTML = [
      '<option value="">All types</option>',
      ...Object.keys(typeLabels).map((type) => `<option value="${{type}}">${{typeLabels[type]}}</option>`)
    ].join("");

    function uniqueSortedValues(field) {{
      return [...new Set(rows.map((row) => row[field]).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    }}

    personaFocus.innerHTML = [
      '<option value="">All personas</option>',
      ...uniqueSortedValues("persona").map((ref) => `<option value="${{ref}}">${{ref}}</option>`)
    ].join("");

    featureFocus.innerHTML = [
      '<option value="">All features</option>',
      ...uniqueSortedValues("feature").map((ref) => `<option value="${{ref}}">${{ref}}</option>`)
    ].join("");

    const rowOptions = ['<option value="">All rows</option>'];
    rows.forEach((row, index) => {{
      const parts = [row.persona, row.story_map, row.page, row.feature, row.gwt].filter(Boolean);
      rowOptions.push(`<option value="${{index}}">Row ${{index + 1}}: ${{parts.join(" -> ")}}</option>`);
    }});
    rowFilter.innerHTML = rowOptions.join("");

    const legend = document.getElementById("legend");
    Object.entries(typeLabels).forEach(([type, label]) => {{
      const item = document.createElement("div");
      item.className = "legend-item";
      item.innerHTML = `<span class="swatch" style="background:${{colors[type]}}"></span><span>${{label}}</span>`;
      legend.appendChild(item);
    }});

    const nodeLayout = new Map();
    nodes.forEach((node) => {{
      nodeLayout.set(node.ref, node.layout);
    }});

    const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svg.append(edgeLayer, nodeLayer);

    const edgeEls = [];
    edges.forEach((edge) => {{
      const from = nodeLayout.get(edge.from);
      const to = nodeLayout.get(edge.to);
      if (!from || !to) return;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const startX = from.x + from.width;
      const startY = from.y + from.height / 2;
      const endX = to.x;
      const endY = to.y + to.height / 2;
      const delta = Math.max(48, Math.abs(endX - startX) * 0.35);
      path.setAttribute("d", `M ${{startX}} ${{startY}} C ${{startX + delta}} ${{startY}}, ${{endX - delta}} ${{endY}}, ${{endX}} ${{endY}}`);
      path.setAttribute("class", `edge${{edge.is_hard ? " hard" : ""}}`);
      path.dataset.from = edge.from;
      path.dataset.to = edge.to;
      path.dataset.type = edge.type;
      edgeLayer.appendChild(path);
      edgeEls.push({{ edge, el: path }});
    }});

    const nodeEls = [];
    nodes.forEach((node) => {{
      const point = nodeLayout.get(node.ref);
      if (!point) return;
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("class", "node");
      group.dataset.ref = node.ref;
      group.dataset.type = node.type;

      const link = document.createElementNS("http://www.w3.org/2000/svg", "a");
      link.setAttribute("href", node.analysis_link);
      link.setAttribute("target", "_blank");
      link.setAttribute("class", "node-link");

      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", point.x);
      rect.setAttribute("y", point.y);
      rect.setAttribute("width", point.width);
      rect.setAttribute("height", point.height);
      rect.setAttribute("class", "node-card");
      rect.setAttribute("stroke", colors[node.type] || "#888");

      const typeText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      typeText.setAttribute("x", point.x + 14);
      typeText.setAttribute("y", point.y + 18);
      typeText.setAttribute("class", "node-type");
      typeText.textContent = typeLabels[node.type] || node.type;

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", point.x + 14);
      label.setAttribute("y", point.y + 39);
      label.setAttribute("class", "node-label");
      label.textContent = node.ref;

      link.append(rect, typeText, label);
      group.appendChild(link);
      group.addEventListener("click", (event) => {{
        event.preventDefault();
        setActiveNode(node.ref);
      }});
      nodeLayer.appendChild(group);
      nodeEls.push({{ node, el: group }});
    }});

    let activeRef = "";

    function collectPathContext(seedRef, scope) {{
      if (!seedRef || !nodeMap.has(seedRef)) {{
        return {{
          refs: new Set(),
          edges: new Set(),
        }};
      }}
      const seedNode = nodeMap.get(seedRef);
      const upstreamRefs = new Set([seedRef, ...(seedNode.upstream_refs || [])]);
      const downstreamRefs = new Set([seedRef, ...(seedNode.downstream_refs || [])]);
      const includeUpstream = scope === "both" || scope === "upstream";
      const includeDownstream = scope === "both" || scope === "downstream";
      const refs = new Set([
        ...(includeUpstream ? [...upstreamRefs] : []),
        ...(includeDownstream ? [...downstreamRefs] : []),
      ]);
      const edgeKeys = new Set();
      edges.forEach((edge) => {{
        if (
          (includeUpstream && upstreamRefs.has(edge.from) && upstreamRefs.has(edge.to)) ||
          (includeDownstream && downstreamRefs.has(edge.from) && downstreamRefs.has(edge.to))
        ) {{
          edgeKeys.add(`${{edge.from}}|${{edge.to}}|${{edge.type}}|${{edge.is_hard}}`);
        }}
      }});
      return {{ refs, edges: edgeKeys }};
    }}

    function applyQueryParams() {{
      const searchValue = params.get("search");
      const personaValue = params.get("persona");
      const featureValue = params.get("feature");
      const typeValue = params.get("type");
      const rowValue = params.get("row");
      const pathScopeValue = params.get("path_scope");
      const hardValue = params.get("hardOnly");
      const focusRef = params.get("focus_ref");

      if (searchValue) search.value = searchValue;
      if (personaValue && [...personaFocus.options].some((option) => option.value === personaValue)) {{
        personaFocus.value = personaValue;
      }}
      if (featureValue && [...featureFocus.options].some((option) => option.value === featureValue)) {{
        featureFocus.value = featureValue;
      }}
      if (typeValue && [...typeFilter.options].some((option) => option.value === typeValue)) {{
        typeFilter.value = typeValue;
      }}
      if (rowValue && [...rowFilter.options].some((option) => option.value === rowValue)) {{
        rowFilter.value = rowValue;
      }}
      if (pathScopeValue && [...pathScope.options].some((option) => option.value === pathScopeValue)) {{
        pathScope.value = pathScopeValue;
      }}
      if (hardValue === "true" || hardValue === "1") {{
        hardOnly.checked = true;
      }}
      if (focusRef && nodeMap.has(focusRef)) {{
        activeRef = focusRef;
      }}
    }}

    function focusRowRefs() {{
      const personaRef = personaFocus.value;
      const featureRef = featureFocus.value;
      const matchingRows = rows.filter((row) => (!personaRef || row.persona === personaRef) && (!featureRef || row.feature === featureRef));
      if (!personaRef && !featureRef) return null;
      return new Set(matchingRows.flatMap((row) => Object.values(row)).filter(Boolean));
    }}

    function activeRowRefs() {{
      if (rowFilter.value === "") return new Set(nodes.map((node) => node.ref));
      const row = rows[Number(rowFilter.value)];
      return new Set(Object.values(row).filter(Boolean));
    }}

    function syncUrlState() {{
      const next = new URLSearchParams();
      if (search.value.trim()) next.set("search", search.value.trim());
      if (personaFocus.value) next.set("persona", personaFocus.value);
      if (featureFocus.value) next.set("feature", featureFocus.value);
      if (typeFilter.value) next.set("type", typeFilter.value);
      if (rowFilter.value) next.set("row", rowFilter.value);
      if (pathScope.value && pathScope.value !== "both") next.set("path_scope", pathScope.value);
      if (hardOnly.checked) next.set("hardOnly", "true");
      if (activeRef) next.set("focus_ref", activeRef);
      const query = next.toString();
      const nextUrl = query ? `${{window.location.pathname}}?${{query}}` : window.location.pathname;
      window.history.replaceState(null, "", nextUrl);
    }}

    function updateFilters() {{
      const searchValue = search.value.trim().toLowerCase();
      const typeValue = typeFilter.value;
      const rowRefs = activeRowRefs();
      const focusedRefs = focusRowRefs();
      const visibleRefs = new Set();
      nodeEls.forEach((entry) => {{
        const matchSearch = !searchValue || [entry.node.ref, entry.node.title, entry.node.slug].join(" ").toLowerCase().includes(searchValue);
        const matchType = !typeValue || entry.node.type === typeValue;
        const matchRow = rowRefs.has(entry.node.ref);
        const matchFocus = !focusedRefs || focusedRefs.has(entry.node.ref);
        const visible = matchSearch && matchType && matchRow && matchFocus;
        entry.el.classList.toggle("hidden", !visible);
        if (visible) visibleRefs.add(entry.node.ref);
      }});
      edgeEls.forEach((entry) => {{
        const visible = visibleRefs.has(entry.edge.from) && visibleRefs.has(entry.edge.to) && (!hardOnly.checked || entry.edge.is_hard);
        entry.el.classList.toggle("hidden", !visible);
      }});
      visibleCount.textContent = String(visibleRefs.size);
      setActiveNode(activeRef);
      syncUrlState();
    }}

    function setActiveNode(ref) {{
      activeRef = ref || "";
      const pathContext = collectPathContext(activeRef, pathScope.value);
      nodeEls.forEach((entry) => {{
        const isSeed = activeRef && entry.node.ref === activeRef;
        const inPath = activeRef && pathContext.refs.has(entry.node.ref);
        entry.el.classList.toggle("active", Boolean(isSeed));
        entry.el.classList.toggle("path-active", Boolean(inPath));
      }});
      edgeEls.forEach((entry) => {{
        const edgeKey = `${{entry.edge.from}}|${{entry.edge.to}}|${{entry.edge.type}}|${{entry.edge.is_hard}}`;
        entry.el.classList.toggle("path-active", activeRef && pathContext.edges.has(edgeKey));
      }});
      if (!activeRef || !nodeMap.has(activeRef)) {{
        detailTitle.textContent = "Select a node";
        detailRef.textContent = "Click a node card to inspect it.";
        detailList.innerHTML = "";
        syncUrlState();
        return;
      }}
      const node = nodeMap.get(activeRef);
      const incoming = edges.filter((edge) => edge.to === activeRef);
      const outgoing = edges.filter((edge) => edge.from === activeRef);
      detailTitle.textContent = node.title;
      detailRef.textContent = node.ref;
      detailList.innerHTML = [
        `<li><strong>Type</strong><br><span class="muted">${{escapeHtml(typeLabels[node.type] || node.type)}}</span></li>`,
        `<li><strong>Round / Status</strong><br><span class="muted">${{escapeHtml(`${{node.round}} / ${{node.status}}`)}}</span></li>`,
        `<li><strong>Source</strong><br><a class="detail-link mono" href="${{escapeHtml(node.analysis_link)}}" target="_blank">${{escapeHtml(node.source_path)}}</a></li>`,
        `<li><strong>Incoming</strong><br><span class="muted mono">${{incoming.length ? incoming.map((edge) => escapeHtml(edge.from)).join("<br>") : "None"}}</span></li>`,
        `<li><strong>Outgoing</strong><br><span class="muted mono">${{outgoing.length ? outgoing.map((edge) => escapeHtml(edge.to)).join("<br>") : "None"}}</span></li>`
      ].join("");
      syncUrlState();
    }}

    search.addEventListener("input", updateFilters);
    personaFocus.addEventListener("change", updateFilters);
    featureFocus.addEventListener("change", updateFilters);
    typeFilter.addEventListener("change", updateFilters);
    rowFilter.addEventListener("change", updateFilters);
    pathScope.addEventListener("change", updateFilters);
    hardOnly.addEventListener("change", updateFilters);
    applyQueryParams();
    updateFilters();
  </script>
</body>
</html>
"""
