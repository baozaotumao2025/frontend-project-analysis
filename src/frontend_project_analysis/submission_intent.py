from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SubmissionIntent:
    kind: str
    confidence: str


_MAINTAINER_PUBLISH_PATTERNS = (
    r"\bskill\b.*\bpublish\b",
    r"\bpublish\b.*\bskill\b",
    r"\bmaintainer\b.*\bpublish\b",
    r"\brelease\b.*\bskill\b",
    r"发布.*skill",
    r"skill.*发布",
    r"发布.*仓库",
    r"仓库.*发布",
)

_DOWNSTREAM_SUBMIT_PATTERNS = (
    r"\bdownstream\b.*\bsubmit\b",
    r"\bsubmit\b.*\bdownstream\b",
    r"\bgenerated\b.*\bsubmit\b",
    r"\bsubmit\b.*\bgenerated\b",
    r"\bcurrent\b.*\bsubmission\b",
    r"\bcurrent\b.*\bgenerated\b",
    r"提交.*生成物",
    r"生成物.*提交",
    r"提交.*当前",
    r"当前.*提交",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def classify_submission_intent(text: str) -> SubmissionIntent | None:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return None

    publish = _matches_any(normalized, _MAINTAINER_PUBLISH_PATTERNS)
    submit = _matches_any(normalized, _DOWNSTREAM_SUBMIT_PATTERNS)

    if publish and not submit:
        return SubmissionIntent(kind="maintainer_publish", confidence="high")
    if submit and not publish:
        return SubmissionIntent(kind="downstream_submit", confidence="high")
    return None
