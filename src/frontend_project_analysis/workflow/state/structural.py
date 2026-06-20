"""Structural workflow checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ...core.domain import REQUIRED_FRONTMATTER_FIELDS, ROUND_BY_TYPE, ArtifactStatus, ArtifactType
from ...infrastructure.documents import read_document
from ...models import Project
from .definitions import CheckFinding, WorkflowStateError

_STRUCTURED_FRONTMATTER_TYPES = {
    ArtifactType.PERSONA,
    ArtifactType.STORY_MAP,
    ArtifactType.PAGE,
    ArtifactType.FEATURE,
}
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_REFERENCE_ALIAS_KEYS = ("aliases", "alias", "display_names", "alternate_titles")


def run_structural_checks(
    session: Session,
    project: Project,
    target_ref: str | None = None,
) -> list[CheckFinding]:
    from ...repositories.dependencies import artifact_ref, assert_no_cycles, list_artifacts

    artifacts = list_artifacts(session, project)
    artifact_map = {artifact_ref(item): item for item in artifacts}
    if target_ref and target_ref not in artifact_map:
        raise WorkflowStateError(
            f"Artifact '{target_ref}' was not found in project '{project.key}'."
        )
    selected = [artifact_map[target_ref]] if target_ref else artifacts
    findings: list[CheckFinding] = []

    try:
        assert_no_cycles(session, project)
    except WorkflowStateError as exc:
        findings.append(CheckFinding(severity="FAIL", code="dependency_cycle", message=str(exc)))

    for artifact in selected:
        ref = artifact_ref(artifact)
        if artifact.round != ROUND_BY_TYPE[artifact.artifact_type]:
            findings.append(
                CheckFinding(
                    severity="FAIL",
                    code="round_mismatch",
                    message=(
                        f"Round {artifact.round} does not match {artifact.artifact_type.value}."
                    ),
                    artifact_ref=ref,
                )
            )
        if artifact.source_path:
            source = Path(project.root_path) / artifact.source_path
            if not source.exists():
                findings.append(
                    CheckFinding(
                        severity="FAIL",
                        code="missing_source",
                        message=f"Source file '{artifact.source_path}' does not exist.",
                        artifact_ref=ref,
                    )
                )
                continue

            metadata, body = read_document(source)
            if artifact.artifact_type in _STRUCTURED_FRONTMATTER_TYPES:
                missing = [field for field in REQUIRED_FRONTMATTER_FIELDS if field not in metadata]
                if missing:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="missing_frontmatter_fields",
                            message=f"Missing frontmatter fields: {', '.join(missing)}.",
                            artifact_ref=ref,
                        )
                    )
                if (
                    metadata.get("artifact_type")
                    and metadata["artifact_type"] != artifact.artifact_type.value
                ):
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="artifact_type_mismatch",
                            message=(
                                "Frontmatter artifact_type does not match database artifact type."
                            ),
                            artifact_ref=ref,
                        )
                    )
                if metadata.get("slug") and metadata["slug"] != artifact.slug:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="slug_mismatch",
                            message="Frontmatter slug does not match database slug.",
                            artifact_ref=ref,
                        )
                    )
                if metadata.get("round") and int(metadata["round"]) != artifact.round:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="round_frontmatter_mismatch",
                            message="Frontmatter round does not match database round.",
                            artifact_ref=ref,
                        )
                    )
                if metadata.get("project") and metadata["project"] != project.key:
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="project_mismatch",
                            message="Frontmatter project does not match selected project key.",
                            artifact_ref=ref,
                        )
                    )

            if artifact.artifact_type == ArtifactType.STORY_MAP:
                _append_missing_sections(
                    findings,
                    ref,
                    body,
                    "missing_story_map_sections",
                    ("Start", "End"),
                    "Story Map",
                )
            elif artifact.artifact_type == ArtifactType.PAGE:
                _append_missing_sections(
                    findings,
                    ref,
                    body,
                    "missing_page_sections",
                    (
                        "Route Information",
                        "Accessible Persona",
                        "Story Steps Covered",
                        "Related Features",
                    ),
                    "Page",
                )
                if not _has_any_section(body, ("Page Responsibility", "Responsibility")):
                    findings.append(
                        CheckFinding(
                            severity="FAIL",
                            code="missing_page_responsibility",
                            message=(
                                "Missing clear page responsibility statement: "
                                "expected either 'Page Responsibility' or 'Responsibility'."
                            ),
                            artifact_ref=ref,
                        )
                    )
                _append_unknown_references(
                    findings,
                    ref,
                    _section_items(body, "Accessible Persona"),
                    ArtifactType.PERSONA,
                    artifacts,
                    "accessible persona",
                )
                _append_unknown_references(
                    findings,
                    ref,
                    _section_items(body, "Related Features"),
                    ArtifactType.FEATURE,
                    artifacts,
                    "related feature",
                )
            elif artifact.artifact_type == ArtifactType.FEATURE:
                _append_missing_sections(
                    findings,
                    ref,
                    body,
                    "missing_feature_sections",
                    (
                        "Page",
                        "Persona Served",
                        "Business Responsibility",
                        "State Type",
                        "Cross-Page Reuse",
                        "Source Story",
                    ),
                    "Feature",
                )
                _append_unknown_references(
                    findings,
                    ref,
                    _section_items(body, "Page"),
                    ArtifactType.PAGE,
                    artifacts,
                    "page",
                )
                _append_unknown_references(
                    findings,
                    ref,
                    _section_items(body, "Persona Served"),
                    ArtifactType.PERSONA,
                    artifacts,
                    "persona",
                )
            elif artifact.artifact_type == ArtifactType.GWT:
                _append_missing_gherkin_scenarios(
                    findings,
                    ref,
                    body,
                    (
                        "Happy Path",
                        "Permission Case",
                        "Error Case",
                        "Edge Case",
                        "Accessibility Case",
                    ),
                )
                _append_incomplete_gherkin_scenarios(findings, ref, body)
            elif artifact.artifact_type == ArtifactType.FEATURE_SPEC:
                _append_missing_sections(
                    findings,
                    ref,
                    body,
                    "missing_feature_spec_sections",
                    (
                        "Basic Information",
                        "Discovery And Evidence",
                        "Risks And Assumptions",
                        "Roles And Permissions",
                        "Component Breakdown",
                        "State Boundary",
                        "Accessibility",
                        "Observability",
                        "Release And Compliance",
                        "Cross-Feature Dependencies",
                        "Given-When-Then Acceptance Spec",
                    ),
                    "Feature Spec",
                )
                _append_state_boundary_terms(findings, ref, body)

        for dependency in artifact.outgoing_dependencies:
            if dependency.is_hard and dependency.to_artifact.status != ArtifactStatus.APPROVED:
                findings.append(
                    CheckFinding(
                        severity="FAIL",
                        code="unapproved_dependency",
                        message=(
                            "Hard dependency "
                            f"'{artifact_ref(dependency.to_artifact)}' is not approved."
                        ),
                        artifact_ref=ref,
                    )
                )
    return findings


def _append_missing_sections(
    findings: list[CheckFinding],
    artifact_ref: str,
    body: str,
    code: str,
    headings: tuple[str, ...],
    label: str,
) -> None:
    normalized_body = body.replace("\r\n", "\n")
    missing = [heading for heading in headings if f"## {heading}" not in normalized_body]
    if missing:
        findings.append(
            CheckFinding(
                severity="FAIL",
                code=code,
                message=f"Missing required {label} sections: {', '.join(missing)}.",
                artifact_ref=artifact_ref,
            )
        )


def _has_any_section(body: str, headings: tuple[str, ...]) -> bool:
    normalized_body = body.replace("\r\n", "\n")
    return any(f"## {heading}" in normalized_body for heading in headings)


def _section_items(body: str, heading: str) -> list[str]:
    lines = _split_body_sections(body).get(_normalize_heading(heading), [])
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        else:
            items.append(stripped)
    return items


def _split_body_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.replace("\r\n", "\n").splitlines():
        if line.startswith("## "):
            current = _normalize_heading(line[3:].strip())
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _normalize_heading(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _append_unknown_references(
    findings: list[CheckFinding],
    artifact_ref: str,
    items: list[str],
    expected_type: ArtifactType,
    artifacts: list,
    label: str,
) -> None:
    known_labels = {
        normalized
        for artifact in artifacts
        if artifact.artifact_type == expected_type
        for normalized in _reference_labels_for_artifact(artifact)
    }
    unknown = [item for item in items if not _reference_item_matches(item, known_labels)]
    if unknown:
        findings.append(
            CheckFinding(
                severity="FAIL",
                code=f"unknown_{expected_type.value}_reference",
                message=(f"Unknown {label} reference(s): {', '.join(unknown)}."),
                artifact_ref=artifact_ref,
            )
        )


def _append_missing_gherkin_scenarios(
    findings: list[CheckFinding],
    artifact_ref: str,
    body: str,
    scenario_names: tuple[str, ...],
) -> None:
    normalized_body = body.replace("\r\n", "\n")
    missing = [name for name in scenario_names if f"Scenario: {name}" not in normalized_body]
    if missing:
        findings.append(
            CheckFinding(
                severity="FAIL",
                code="missing_gwt_scenarios",
                message=f"Missing required GWT scenarios: {', '.join(missing)}.",
                artifact_ref=artifact_ref,
            )
        )


def _append_incomplete_gherkin_scenarios(
    findings: list[CheckFinding],
    artifact_ref: str,
    body: str,
) -> None:
    normalized = body.replace("\r\n", "\n")
    scenario_headers = list(
        re.finditer(r"^  Scenario:\s*(.+?)\s*$", normalized, flags=re.MULTILINE)
    )
    if not scenario_headers:
        return
    missing_steps: list[str] = []
    for index, header in enumerate(scenario_headers):
        start = header.end()
        end = (
            scenario_headers[index + 1].start()
            if index + 1 < len(scenario_headers)
            else len(normalized)
        )
        block = normalized[start:end]
        present = {
            "Given": "Given" in block,
            "When": "When" in block,
            "Then": "Then" in block,
        }
        for step, has_step in present.items():
            if not has_step:
                missing_steps.append(f"{header.group(1).strip()}: {step}")
    if missing_steps:
        findings.append(
            CheckFinding(
                severity="FAIL",
                code="incomplete_gwt_scenarios",
                message=(
                    "Each GWT scenario must include Given, When, and Then; missing "
                    f"{', '.join(missing_steps)}."
                ),
                artifact_ref=artifact_ref,
            )
        )


def _append_state_boundary_terms(
    findings: list[CheckFinding],
    artifact_ref: str,
    body: str,
) -> None:
    sections = _split_body_sections(body)
    lines = sections.get(_normalize_heading("State Boundary"), [])
    text = "\n".join(line.strip() for line in lines if line.strip()).lower()
    missing_terms = [term for term in ("server state", "client state") if term not in text]
    if missing_terms:
        findings.append(
            CheckFinding(
                severity="FAIL",
                code="missing_state_boundary_terms",
                message=(
                    "State Boundary must explicitly separate server state and client state: "
                    f"{', '.join(missing_terms)} missing."
                ),
                artifact_ref=artifact_ref,
            )
        )


def _normalize_reference_label(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _reference_item_matches(item: str, known_labels: set[str]) -> bool:
    return any(
        normalized in known_labels
        for normalized in _normalized_reference_candidates(item)
        if normalized
    )


def _normalized_reference_candidates(item: str) -> set[str]:
    candidates: set[str] = set()
    stripped = item.strip()
    if not stripped:
        return candidates
    candidates.add(_normalize_reference_label(stripped))
    for link_text, link_target in _MARKDOWN_LINK_RE.findall(stripped):
        normalized_text = _normalize_reference_label(link_text)
        if normalized_text:
            candidates.add(normalized_text)
        normalized_target = _normalize_reference_label(_reference_target_label(link_target))
        if normalized_target:
            candidates.add(normalized_target)
    if _MARKDOWN_LINK_RE.search(stripped):
        linkless = _MARKDOWN_LINK_RE.sub(lambda match: match.group(1).strip(), stripped)
        normalized_linkless = _normalize_reference_label(linkless)
        if normalized_linkless:
            candidates.add(normalized_linkless)
    return candidates


def _reference_target_label(target: str) -> str:
    cleaned = target.strip().strip("<>")
    if not cleaned:
        return ""
    cleaned = cleaned.split("?", 1)[0].split("#", 1)[0]
    return Path(cleaned).stem


def _reference_labels_for_artifact(artifact: Any) -> set[str]:
    labels = {
        _normalize_reference_label(artifact.slug),
        _normalize_reference_label(artifact.title),
    }
    metadata = getattr(artifact, "metadata_json", {}) or {}
    for key in _REFERENCE_ALIAS_KEYS:
        value = metadata.get(key)
        if isinstance(value, str):
            labels.add(_normalize_reference_label(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    labels.add(_normalize_reference_label(item))
    return {label for label in labels if label}
