"""Domain enums and constants."""

from __future__ import annotations

from enum import StrEnum


class ArtifactType(StrEnum):
    PERSONA = "persona"
    STORY_MAP = "story_map"
    PAGE = "page"
    FEATURE = "feature"
    GWT = "gwt"
    FEATURE_SPEC = "feature_spec"


class ArtifactStatus(StrEnum):
    DRAFT = "draft"
    STRUCTURALLY_VALID = "structurally_valid"
    SEMANTIC_REVIEW = "semantic_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    STALE = "stale"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class DependencyType(StrEnum):
    REQUIRES = "requires"
    DERIVED_FROM = "derived_from"
    COVERS = "covers"
    SERVES = "serves"
    IMPLEMENTS = "implements"
    SUPERCEDES = "supersedes"


class ReviewKind(StrEnum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"


class ReviewStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_REVISION = "needs_revision"


class ReviewerKind(StrEnum):
    RULE_ENGINE = "rule_engine"
    LLM = "llm"
    HUMAN = "human"


ROUND_BY_TYPE: dict[ArtifactType, int] = {
    ArtifactType.PERSONA: 1,
    ArtifactType.STORY_MAP: 2,
    ArtifactType.PAGE: 3,
    ArtifactType.FEATURE: 4,
    ArtifactType.GWT: 5,
    ArtifactType.FEATURE_SPEC: 6,
}


REQUIRED_FRONTMATTER_FIELDS = ("artifact_type", "slug", "round", "status", "project")


SEMANTIC_REVIEW_RUBRICS: dict[ArtifactType, list[str]] = {
    ArtifactType.PERSONA: [
        "Role boundaries are concrete rather than generic job titles.",
        "Core goals differ materially from other Persona entries.",
        "Permission boundaries align with the described business model.",
    ],
    ArtifactType.STORY_MAP: [
        "Activities describe real user goals rather than UI click sequences.",
        "The flow has a business-valid start and end.",
        "Stories stay in behavior space and do not leak pages or Features.",
    ],
    ArtifactType.PAGE: [
        "Mapped surfaces cover the intended Story Steps without orphan gaps.",
        "Shared surfaces are represented once with clear Persona coverage.",
        "Page boundaries avoid mixing unrelated jobs to be done.",
    ],
    ArtifactType.FEATURE: [
        "The slice has an independent business purpose.",
        "The slice has an independently testable behavior boundary.",
        "The split minimizes unnecessary coupling to adjacent Features.",
    ],
    ArtifactType.GWT: [
        "Scenarios cover Happy Path, Permission Case, Error Case, and Edge Case.",
        "Given/When/Then remain declarative and business-facing.",
        "Scenarios align with the approved Feature boundary.",
    ],
    ArtifactType.FEATURE_SPEC: [
        "The spec keeps implementation boundaries explicit and stable.",
        "Dependencies are correctly called out and do not hide coupling.",
        "State responsibilities are separated clearly enough for delivery.",
    ],
}


def semantic_review_to_artifact_status(
    decision: ReviewStatus,
    auto_approve: bool = False,
) -> ArtifactStatus:
    """Map a semantic review decision to the next artifact lifecycle status.

    `semantic_review` is the post-review holding state: it means the artifact has
    completed semantic review and is waiting for explicit human approval unless
    auto-approval is enabled.
    """

    if decision == ReviewStatus.FAILED:
        return ArtifactStatus.REJECTED
    if decision == ReviewStatus.PASSED and auto_approve:
        return ArtifactStatus.APPROVED
    return ArtifactStatus.SEMANTIC_REVIEW
