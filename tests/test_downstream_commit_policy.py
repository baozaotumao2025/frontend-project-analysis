from __future__ import annotations

import pytest

from frontend_project_analysis.downstream_commit_policy import (
    ALLOWED_DOWNSTREAM_COMMIT_TYPES,
    parse_downstream_commit_message,
    validate_downstream_commit_message,
)


def test_downstream_commit_policy_accepts_generated_project_type() -> None:
    message = "sync(readme): align generated release guidance"

    parsed = parse_downstream_commit_message(message)

    assert parsed is not None
    assert parsed.type in ALLOWED_DOWNSTREAM_COMMIT_TYPES
    assert parsed.scope == "readme"
    assert parsed.summary == "align generated release guidance"
    assert validate_downstream_commit_message(message) == []


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (
            "feat(readme): align generated release guidance",
            "Unsupported downstream commit type",
        ),
        (
            "docs: align generated release guidance",
            "Commit message must use <type>(<scope>): <summary>",
        ),
    ],
)
def test_downstream_commit_policy_rejects_default_or_malformed_types(
    message: str,
    expected: str,
) -> None:
    issues = validate_downstream_commit_message(message)

    assert issues
    assert any(expected in issue for issue in issues)

