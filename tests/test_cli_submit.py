from __future__ import annotations

import json
from pathlib import Path

from tests.cli_support import invoke_with_root


def test_submit_command_routes_to_maintainer_publish(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    monkeypatch.setenv("FPA_LLM_MODEL", "mock-model")

    result = invoke_with_root(tmp_path, ["submit", "Please publish the skill repository"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["command"] == "submit"
    assert payload["intent"] == "maintainer_publish"
    assert payload["suggested_action"] == "Proceed with maintainer publish flow."


def test_submit_command_routes_to_downstream_submit(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    monkeypatch.setenv("FPA_LLM_MODEL", "mock-model")

    result = invoke_with_root(tmp_path, ["submit", "帮我提交当前生成物"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["command"] == "submit"
    assert payload["intent"] == "downstream_submit"
    assert payload["suggested_action"] == "Proceed with downstream submit flow."


def test_submit_command_rejects_ambiguous_request(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FPA_LLM_PROVIDER", "mock")
    monkeypatch.setenv("FPA_LLM_MODEL", "mock-model")

    result = invoke_with_root(tmp_path, ["submit", "请帮我处理一下"])

    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["intent"] == "ambiguous"
    assert payload["suggested_action"] == "Ask a clarifying question about the target repository."
