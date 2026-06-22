"""Declarative packet spec definitions."""

from __future__ import annotations

from .brief import BRIEF_ASSISTANT_SPEC
from .release import RELEASE_REVIEW_SPEC
from .review import REVIEW_LLM_CONTEXT_SPEC
from .submission import SUBMISSION_ROUTER_SPEC

PACKET_SPECS = {
    REVIEW_LLM_CONTEXT_SPEC.name: REVIEW_LLM_CONTEXT_SPEC,
    BRIEF_ASSISTANT_SPEC.name: BRIEF_ASSISTANT_SPEC,
    SUBMISSION_ROUTER_SPEC.name: SUBMISSION_ROUTER_SPEC,
    RELEASE_REVIEW_SPEC.name: RELEASE_REVIEW_SPEC,
}
