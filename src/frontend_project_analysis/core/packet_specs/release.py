"""Release review packet spec."""

from __future__ import annotations

from ..packet_types import PacketSpec
from ..prompts import build_release_review_packet_manifest

RELEASE_REVIEW_SPEC = PacketSpec(
    name="release_review",
    description="Release review packet",
    builder=build_release_review_packet_manifest,
    required_keys=(
        "review_kind",
        "fresh_session_required",
        "packet_only",
        "review_isolation",
        "response_format",
        "findings_order",
        "focus",
        "repository_context",
        "changed_surface_count",
        "prompt_rules",
        "audit_focus",
    ),
    isolation_key="review_isolation",
    isolation_mode="fresh_release_reviewer_context",
)
