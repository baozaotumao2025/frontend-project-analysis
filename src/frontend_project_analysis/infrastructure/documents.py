"""Markdown/frontmatter helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from ..core.domain import ArtifactType


def read_document(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    try:
        _, frontmatter, body = text.split("---\n", 2)
    except ValueError:
        return {}, text
    metadata = yaml.safe_load(frontmatter) or {}
    return metadata, body.lstrip("\n")


def compute_content_hash(metadata: dict[str, Any], body: str) -> str:
    payload = yaml.safe_dump(metadata, sort_keys=True) + "\n" + body
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def infer_artifact_type(path: Path) -> ArtifactType | None:
    normalized = path.as_posix()
    if "/docs/personas/" in normalized:
        return ArtifactType.PERSONA
    if "/docs/story-maps/" in normalized:
        return ArtifactType.STORY_MAP
    if "/docs/pages/" in normalized:
        return ArtifactType.PAGE
    if "/docs/features/" in normalized:
        return ArtifactType.FEATURE
    if "/docs/gwt/" in normalized:
        return ArtifactType.GWT
    if "/specs/features/" in normalized:
        return ArtifactType.FEATURE_SPEC
    return None
