"""Helpers for brief provenance and confirmation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml

from ..infrastructure.documents import compute_content_hash

BRIEF_FORMAT_VERSION = 1
BRIEF_STATUS_DRAFT = "draft"
BRIEF_STATUS_CONFIRMED = "confirmed"

BRIEF_SOURCE_USER = "user"
BRIEF_SOURCE_INTERVIEW = "brief_interview"
BRIEF_SOURCE_ASSISTANT = "brief_assistant"

BRIEF_FRONTMATTER_PREFIX = "---\n"


@dataclass(frozen=True)
class BriefProvenance:
    source_kind: str
    status: str
    confirmed_by_user: bool
    body_hash: str
    format_version: int = BRIEF_FORMAT_VERSION


def normalize_brief_body(body: str) -> str:
    return body.strip() + "\n"


def compute_brief_body_hash(body: str) -> str:
    normalized_body = normalize_brief_body(body)
    return compute_content_hash({}, normalized_body)


def split_brief_text(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    try:
        _, frontmatter, body = text.split("---\n", 2)
    except ValueError:
        return {}, text
    metadata = yaml.safe_load(frontmatter) or {}
    return metadata, body.lstrip("\n")


def render_brief_document(
    body: str,
    *,
    source_kind: str,
    status: str,
    confirmed_by_user: bool,
    title: str = "Project Brief",
    extra_metadata: Mapping[str, Any] | None = None,
) -> str:
    normalized_body = normalize_brief_body(body)
    metadata: dict[str, Any] = {
        "brief_body_sha256": compute_brief_body_hash(normalized_body),
        "brief_confirmed_by_user": confirmed_by_user,
        "brief_format": "v1",
        "brief_source_kind": source_kind,
        "brief_status": status,
        "title": title,
    }
    if extra_metadata:
        metadata.update(dict(extra_metadata))
    frontmatter = yaml.safe_dump(metadata, sort_keys=True).strip()
    return f"---\n{frontmatter}\n---\n\n{normalized_body}"


def read_brief_provenance(metadata: Mapping[str, Any], body: str) -> BriefProvenance:
    source_kind = str(metadata.get("brief_source_kind") or BRIEF_SOURCE_USER)
    status = str(metadata.get("brief_status") or BRIEF_STATUS_DRAFT)
    confirmed_by_user = bool(metadata.get("brief_confirmed_by_user"))
    body_hash = str(metadata.get("brief_body_sha256") or "")
    return BriefProvenance(
        source_kind=source_kind,
        status=status,
        confirmed_by_user=confirmed_by_user,
        body_hash=body_hash or compute_brief_body_hash(body),
        format_version=int(metadata.get("brief_format_version") or BRIEF_FORMAT_VERSION),
    )


def is_confirmed_brief(metadata: Mapping[str, Any], body: str) -> bool:
    provenance = read_brief_provenance(metadata, body)
    if provenance.status != BRIEF_STATUS_CONFIRMED:
        return False
    if not provenance.confirmed_by_user:
        return False
    if provenance.body_hash != compute_brief_body_hash(body):
        return False
    return True


def is_confirmed_brief_text(text: str) -> bool:
    metadata, body = split_brief_text(text)
    return is_confirmed_brief(metadata, body)


def confirm_brief_metadata(
    metadata: Mapping[str, Any],
    body: str,
    *,
    source_kind: str | None = None,
    confirmed_by_user: bool = True,
) -> dict[str, Any]:
    normalized_body = normalize_brief_body(body)
    existing_source_kind = str(metadata.get("brief_source_kind") or BRIEF_SOURCE_USER)
    return {
        **dict(metadata),
        "brief_body_sha256": compute_brief_body_hash(normalized_body),
        "brief_confirmed_by_user": confirmed_by_user,
        "brief_format": "v1",
        "brief_source_kind": source_kind or existing_source_kind,
        "brief_status": BRIEF_STATUS_CONFIRMED,
        "brief_format_version": BRIEF_FORMAT_VERSION,
    }
