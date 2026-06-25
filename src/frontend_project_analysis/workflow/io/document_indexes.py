"""Documentation index rendering helpers."""

from __future__ import annotations

import re
from pathlib import Path

from ...core.config import ANALYSIS_DIR_NAME
from ...infrastructure.documents import read_document

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_STORY_LINE_RE = re.compile(r"^\s*-\s*Story:\s*(.+?)\s*$", re.MULTILINE)
_ROUTE_LINE_RE = re.compile(r"^\s*-\s*Route:\s*`?(.+?)`?\s*$", re.MULTILINE)


def _normalize_heading(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _split_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        heading_match = _HEADING_RE.match(line)
        if heading_match and len(heading_match.group(1)) <= 3:
            current = _normalize_heading(heading_match.group(2))
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _section_summary(body: str, heading: str) -> str:
    sections = _split_sections(body)
    lines = [line.strip() for line in sections.get(_normalize_heading(heading), [])]
    for line in lines:
        if not line:
            continue
        if line.startswith("- "):
            return line[2:].strip()
        return line
    return ""


def _section_value(body: str, heading: str, pattern: re.Pattern[str] | None = None) -> str:
    sections = _split_sections(body)
    lines = [line.strip() for line in sections.get(_normalize_heading(heading), [])]
    for line in lines:
        if not line:
            continue
        if pattern is not None:
            match = pattern.match(line)
            if match:
                return match.group(1).strip()
        if line.startswith("- "):
            return line[2:].strip()
        return line
    return ""


def _story_map_boundaries(body: str) -> tuple[str, str]:
    start = _section_value(body, "Start")
    end = _section_value(body, "End")
    if start or end:
        return start, end
    stories = [
        match.group(1).strip() for match in _STORY_LINE_RE.finditer(body) if match.group(1).strip()
    ]
    if not stories:
        return "", ""
    return stories[0], stories[-1]


def _first_nonempty_frontmatter_value(metadata: dict, *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in {None, ""}:
            return str(value)
    return ""


def _collect_files(root: Path, relative_dir: str, suffix: str) -> list[Path]:
    base = root / ANALYSIS_DIR_NAME / relative_dir
    if not base.exists():
        return []
    return [
        path
        for path in sorted(base.glob(f"*{suffix}"))
        if path.name != "index.md" and not path.name.endswith("-spec.md")
    ]


def _render_table(title: str, headers: list[str], rows: list[list[str]]) -> str:
    lines = [title, "", f"| {' | '.join(headers)} |", f"| {' | '.join(['---'] * len(headers))} |"]
    for row in rows:
        lines.append(f"| {' | '.join(row)} |")
    return "\n".join(lines) + "\n"


def _link(label: str, target: str) -> str:
    return f"[{label}]({target})"


def _render_root_index() -> str:
    return (
        "# Analysis Index\n\n"
        "## Brief\n\n"
        "- [Project Brief](./brief.md)\n\n"
        "## Personas\n\n"
        "- [Persona Index](./personas/index.md)\n\n"
        "## Story Maps\n\n"
        "- [Story Map Index](./story-maps/index.md)\n\n"
        "## Pages\n\n"
        "- [Page Index](./pages/index.md)\n\n"
        "## Features\n\n"
        "- [Feature Index](./features/index.md)\n\n"
        "## Relations\n\n"
        "- [Relations Index](./relations/index.md)\n"
        "- [Persona Story Page Matrix](./relations/persona-story-page-matrix.md)\n"
        "- [Feature Coverage Matrix](./relations/feature-coverage-matrix.md)\n"
        "- [GWT Feature Matrix](./relations/gwt-feature-matrix.md)\n"
        "- [Relationship Graph](./relations/graph.html)\n"
    )


def _render_relations_index() -> str:
    return (
        "# Relations Index\n\n"
        "## Matrices\n\n"
        "- [Persona Story Page Matrix](./persona-story-page-matrix.md)\n"
        "- [Feature Coverage Matrix](./feature-coverage-matrix.md)\n"
        "- [GWT Feature Matrix](./gwt-feature-matrix.md)\n\n"
        "## Graph Views\n\n"
        "- [Relationship Graph](./graph.html)\n"
    )


def _render_persona_index(root: Path) -> str:
    rows: list[list[str]] = []
    for path in _collect_files(root, "personas", ".md"):
        metadata, body = read_document(path)
        slug = str(metadata.get("slug") or path.stem)
        title = str(metadata.get("title") or slug.replace("-", " ").title())
        persona_link = _link(title, f"./{slug}.md")
        story_map_link = _link(slug, f"../story-maps/{slug}.md")
        core_goal = _section_summary(body, "Core Goal")
        notes = " / ".join(
            item
            for item in (
                _section_summary(body, "Permission Boundary"),
                _section_summary(body, "Invisible Pages Or Capabilities"),
            )
            if item
        )
        rows.append([persona_link, core_goal, story_map_link, notes])
    return _render_table(
        "# Persona Index",
        ["Persona", "Core Goal", "Story Map", "Notes"],
        rows,
    )


def _render_story_map_index(root: Path) -> str:
    rows: list[list[str]] = []
    for path in _collect_files(root, "story-maps", ".md"):
        metadata, body = read_document(path)
        slug = str(metadata.get("slug") or path.stem)
        title = str(metadata.get("title") or slug.replace("-", " ").title())
        persona_name = title.removesuffix(" Story Map")
        start, end = _story_map_boundaries(body)
        rows.append([persona_name, _link(title, f"./{slug}.md"), start, end])
    return _render_table(
        "# Story Map Index",
        ["Persona", "Story Map", "起点", "终点"],
        rows,
    )


def _render_page_index(root: Path) -> str:
    rows: list[list[str]] = []
    for path in _collect_files(root, "pages", ".md"):
        metadata, body = read_document(path)
        slug = str(metadata.get("slug") or path.stem)
        title = str(metadata.get("title") or slug.replace("-", " ").title())
        page_link = _link(title, f"./{slug}.md")
        route = (
            _section_value(body, "Route Information", pattern=_ROUTE_LINE_RE)
            or _first_nonempty_frontmatter_value(metadata, "route", "path")
            or f"/{slug}"
        )
        accessible_persona = _section_summary(body, "Accessible Persona")
        responsibility = _section_summary(body, "Page Responsibility") or _section_summary(
            body, "Responsibility"
        )
        rows.append([route, page_link, accessible_persona, responsibility])
    return _render_table(
        "# Page Index",
        ["Route", "Page Name", "Accessible Persona", "Responsibility"],
        rows,
    )


def _render_feature_index(root: Path) -> str:
    rows: list[list[str]] = []
    for path in _collect_files(root, "features", ".md"):
        metadata, body = read_document(path)
        slug = str(metadata.get("slug") or path.stem)
        title = str(metadata.get("title") or slug.replace("-", " ").title())
        feature_link = _link(title, f"./{slug}.md")
        page = _section_summary(body, "Page")
        persona = _section_summary(body, "Persona Served") or _section_summary(
            body, "Service Persona"
        )
        responsibility = _section_summary(body, "Business Responsibility") or _section_summary(
            body, "Responsibility"
        )
        state_type = _section_summary(body, "State Type")
        cross_page_reuse = _section_summary(body, "Cross-Page Reuse")
        rows.append([feature_link, responsibility, page, persona, state_type, cross_page_reuse])
    return _render_table(
        "# Feature Index",
        ["Feature", "Responsibility", "Page", "Persona Served", "State Type", "Cross-Page Reuse"],
        rows,
    )


def refresh_document_indexes(root: Path) -> list[Path]:
    docs_root = root / ANALYSIS_DIR_NAME
    personas = docs_root / "personas" / "index.md"
    story_maps = docs_root / "story-maps" / "index.md"
    pages = docs_root / "pages" / "index.md"
    features = docs_root / "features" / "index.md"
    relations = docs_root / "relations" / "index.md"
    root_index = docs_root / "index.md"

    docs_root.mkdir(parents=True, exist_ok=True)
    relations.parent.mkdir(parents=True, exist_ok=True)
    root_index.write_text(_render_root_index(), encoding="utf-8")
    personas.write_text(_render_persona_index(root), encoding="utf-8")
    story_maps.write_text(_render_story_map_index(root), encoding="utf-8")
    pages.write_text(_render_page_index(root), encoding="utf-8")
    features.write_text(_render_feature_index(root), encoding="utf-8")
    relations.write_text(_render_relations_index(), encoding="utf-8")
    return [root_index, personas, story_maps, pages, features, relations]
