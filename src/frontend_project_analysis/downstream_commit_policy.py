from __future__ import annotations

from dataclasses import dataclass
import re


ALLOWED_DOWNSTREAM_COMMIT_TYPES = {
    "analysis",
    "policy",
    "release",
    "sync",
    "tooling",
}

_COMMIT_MESSAGE_RE = re.compile(
    r"^(?P<type>[a-z]+)\((?P<scope>[^()]+)\): (?P<summary>.+)$"
)


@dataclass(frozen=True)
class DownstreamCommitMessage:
    type: str
    scope: str
    summary: str


def parse_downstream_commit_message(message: str) -> DownstreamCommitMessage | None:
    match = _COMMIT_MESSAGE_RE.match(message.strip())
    if match is None:
        return None
    return DownstreamCommitMessage(
        type=match.group("type"),
        scope=match.group("scope"),
        summary=match.group("summary"),
    )


def validate_downstream_commit_message(message: str) -> list[str]:
    issues: list[str] = []
    parsed = parse_downstream_commit_message(message)
    if parsed is None:
        return [
            "Commit message must use <type>(<scope>): <summary> with a supported downstream type."
        ]

    if parsed.type not in ALLOWED_DOWNSTREAM_COMMIT_TYPES:
        issues.append(
            f"Unsupported downstream commit type {parsed.type!r}. "
            f"Allowed types: {sorted(ALLOWED_DOWNSTREAM_COMMIT_TYPES)}."
        )

    if not parsed.scope.strip():
        issues.append("Commit scope must not be empty.")

    if not parsed.summary.strip():
        issues.append("Commit summary must not be empty.")

    return issues

