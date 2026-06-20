from __future__ import annotations

import pytest

from frontend_project_analysis.submission_intent import classify_submission_intent


@pytest.mark.parametrize(
    ("text", "expected_kind"),
    [
        ("帮我发布 skill 仓库", "maintainer_publish"),
        ("Please publish the skill repository", "maintainer_publish"),
        ("帮我提交当前生成物", "downstream_submit"),
        ("Please submit the current generated project", "downstream_submit"),
    ],
)
def test_submission_intent_classifies_clear_natural_language_requests(
    text: str,
    expected_kind: str,
) -> None:
    intent = classify_submission_intent(text)

    assert intent is not None
    assert intent.kind == expected_kind
    assert intent.confidence == "high"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "帮我处理一下",
        "请帮我弄好这个项目",
        "publish",
        "submit",
        "帮我发布并提交",
    ],
)
def test_submission_intent_rejects_ambiguous_or_insufficient_input(text: str) -> None:
    assert classify_submission_intent(text) is None

