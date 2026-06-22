from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from frontend_project_analysis.cli import app
from frontend_project_analysis.llm.types import ProviderResponse
from frontend_project_analysis.schemas import BriefAssistantPayload, ProviderAuditPayload
from frontend_project_analysis.workflow.briefs import is_confirmed_brief_text, split_brief_text

pytestmark = pytest.mark.smoke

runner = CliRunner()


def _fake_brief_assistant(packet: dict, settings=None, stage: str = "followup") -> ProviderResponse:
    assert packet["llm_isolation"]["mode"] == "fresh_brief_assistant_context"
    assert packet["llm_isolation"]["fork_context"] is False
    assert packet["llm_isolation"]["required"] is True
    if stage == "followup":
        payload = BriefAssistantPayload(
            stage="followup",
            summary="Follow-up suggestions prepared.",
            reviewer_ref="fake-brief-assistant",
            model="fake-model",
            can_finalize=False,
            confidence="high",
            gaps=["Integration scope is still unclear."],
            recommended_questions=["Which integrations matter most?"],
            draft_brief=None,
        )
    else:
        payload = BriefAssistantPayload(
            stage="summary",
            summary="The brief is coherent enough to draft.",
            reviewer_ref="fake-brief-assistant",
            model="fake-model",
            can_finalize=True,
            confidence="high",
            gaps=["None"],
            recommended_questions=[],
            draft_brief="Draft summary from the AI assistant.",
        )
    audit = ProviderAuditPayload(
        trace_id="trace",
        request_id="request",
        provider_name="mock",
        endpoint="mock://brief",
        call_status="mocked",
        attempt_count=1,
        duration_ms=0,
        request_json={"stage": stage},
    )
    return ProviderResponse(payload=payload, raw_response={"provider": "mock"}, audit=audit)


def test_brief_interview_collects_and_writes_brief(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    result = runner.invoke(
        app,
        ["brief", "interview", "--output", str(output), "--max-questions", "3"],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    metadata, body = split_brief_text(text)
    assert metadata["brief_status"] == "draft"
    assert metadata["brief_confirmed_by_user"] is False
    assert metadata["brief_source_kind"] == "brief_interview"
    assert not is_confirmed_brief_text(text)
    assert body.startswith("# Project Brief")
    assert "# Project Brief" in text
    assert "Manage customer assignments." in text
    assert "Sales reps and operations leads." in text
    assert "Reassign customers and review ownership boundaries." in text
    assert "unknown" in text


def test_brief_interview_supports_dry_run(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    result = runner.invoke(
        app,
        ["brief", "interview", "--output", str(output), "--dry-run", "--max-questions", "3"],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert not output.exists()
    assert "Dry run: brief was not written to disk." in result.output
    assert "# Project Brief" in result.output
    assert "brief_status: draft" in result.output


def test_brief_interview_follows_up_on_vague_answers(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    result = runner.invoke(
        app,
        ["brief", "interview", "--output", str(output), "--max-questions", "5"],
        input=(
            "Customer management.\n"
            "Users.\n"
            "Workflows.\n"
            "The product helps users manage customer data.\n"
            "Sales and operations need it.\n"
            "Users need to complete the customer handoff workflow.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "A few details are still unclear" in result.output
    text = output.read_text(encoding="utf-8")
    metadata, _ = split_brief_text(text)
    assert metadata["brief_status"] == "draft"
    assert "The product helps users manage customer data." in text
    assert "Sales and operations need it." in text
    assert "Users need to complete the customer handoff workflow." not in text
    assert "unknown" in text


def test_brief_interview_respects_max_questions(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    result = runner.invoke(
        app,
        ["brief", "interview", "--output", str(output), "--max-questions", "3"],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    metadata, _ = split_brief_text(text)
    assert metadata["brief_status"] == "draft"
    assert "Manage customer assignments." in text
    assert "Sales reps and operations leads." in text
    assert "Reassign customers and review ownership boundaries." in text


def test_brief_interview_writes_transcript(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    transcript = tmp_path / "brief-transcript.md"
    result = runner.invoke(
        app,
        [
            "brief",
            "interview",
            "--output",
            str(output),
            "--max-questions",
            "3",
            "--transcript",
            str(transcript),
        ],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert output.exists()
    assert transcript.exists()
    transcript_text = transcript.read_text(encoding="utf-8")
    assert "# Brief Interview Transcript" in transcript_text
    assert "1/3 What does the product do?" in transcript_text
    assert "2/3 Who are the main users?" in transcript_text
    assert "3/3 What are the core usage scenarios?" in transcript_text
    assert "Manage customer assignments." in transcript_text
    assert "Sales reps and operations leads." in transcript_text
    assert "Reassign customers and review ownership boundaries." in transcript_text


def test_brief_interview_dry_run_prints_transcript(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    transcript = tmp_path / "brief-transcript.md"
    result = runner.invoke(
        app,
        [
            "brief",
            "interview",
            "--output",
            str(output),
            "--dry-run",
            "--max-questions",
            "3",
            "--transcript",
            str(transcript),
        ],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert not output.exists()
    assert not transcript.exists()
    assert "# Project Brief" in result.output
    assert "brief_status: draft" in result.output
    assert "# Brief Interview Transcript" in result.output
    assert "Dry run: brief was not written to disk." in result.output


def test_brief_interview_respects_total_question_budget(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    transcript = tmp_path / "brief-transcript.md"
    result = runner.invoke(
        app,
        [
            "brief",
            "interview",
            "--output",
            str(output),
            "--max-questions",
            "5",
            "--transcript",
            str(transcript),
        ],
        input=(
            "Customer management.\n"
            "Users.\n"
            "Integrations.\n"
            "The product helps users manage customer data.\n"
            "Sales and operations teams.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    transcript_text = transcript.read_text(encoding="utf-8")
    assert transcript_text.count("## ") == 5
    assert "What constraints or dependencies matter most?" not in transcript_text


def test_brief_interview_collects_cross_cutting_sections(tmp_path: Path) -> None:
    output = tmp_path / "project-brief.md"
    transcript = tmp_path / "brief-transcript.md"
    result = runner.invoke(
        app,
        [
            "brief",
            "interview",
            "--output",
            str(output),
            "--transcript",
            str(transcript),
            "--max-questions",
            "8",
        ],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
            "Customer support notes and onboarding docs.\n"
            "A rollout mismatch could block customer handoffs.\n"
            "Keyboard-only usage must work.\n"
            "Success and failure counts should be measurable.\n"
            "Ship behind a feature flag and support rollback.\n"
        ),
    )

    assert result.exit_code == 0, result.output
    text = output.read_text(encoding="utf-8")
    assert "Customer support notes and onboarding docs." in text
    assert "A rollout mismatch could block customer handoffs." in text
    assert "Keyboard-only usage must work." in text
    assert "Success and failure counts should be measurable." in text
    assert "Ship behind a feature flag and support rollback." in text
    assert "## What evidence supports this brief?" in text
    assert "## What are the biggest risks or assumptions?" in text
    assert "## What accessibility expectations matter?" in text
    assert "## What should we observe after release?" in text
    assert "## What release or compliance constraints matter?" in text
    assert "# Brief Interview Transcript" in transcript.read_text(encoding="utf-8")
    assert transcript.read_text(encoding="utf-8").count("## ") == 8


def test_brief_assistant_mode_adds_ai_sections(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "frontend_project_analysis.commands.brief.run_brief_assistant",
        _fake_brief_assistant,
    )
    output = tmp_path / "project-brief.md"
    transcript = tmp_path / "brief-transcript.md"
    result = runner.invoke(
        app,
        [
            "brief",
            "assistant",
            "--output",
            str(output),
            "--transcript",
            str(transcript),
            "--max-questions",
            "4",
        ],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
            "Which integrations matter most?\n"
        ),
    )

    assert result.exit_code == 0, result.output
    text = output.read_text(encoding="utf-8")
    assert "## AI Assistant Follow-Ups" in text
    assert "Which integrations matter most?" in text
    assert "## AI Assistant Summary" in text
    assert "The brief is coherent enough to draft." in text
    assert "## AI Assistant Draft Brief" in text
    assert "Draft summary from the AI assistant." in text
    transcript_text = transcript.read_text(encoding="utf-8")
    assert "Which integrations matter most?" in transcript_text


def test_brief_interview_llm_assist_option(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "frontend_project_analysis.commands.brief.run_brief_assistant",
        _fake_brief_assistant,
    )
    output = tmp_path / "project-brief.md"
    result = runner.invoke(
        app,
        [
            "brief",
            "interview",
            "--llm-assist",
            "--output",
            str(output),
            "--max-questions",
            "4",
        ],
        input=(
            "Manage customer assignments.\n"
            "Sales reps and operations leads.\n"
            "Reassign customers and review ownership boundaries.\n"
            "Which integrations matter most?\n"
        ),
    )

    assert result.exit_code == 0, result.output
    text = output.read_text(encoding="utf-8")
    metadata, _ = split_brief_text(text)
    assert metadata["brief_status"] == "draft"
    assert "## AI Assistant Summary" in text
    assert "Which integrations matter most?" in text


def test_brief_confirm_marks_draft_as_confirmed(tmp_path: Path) -> None:
    draft = tmp_path / "draft-brief.md"
    draft.write_text(
        "---\n"
        "brief_confirmed_by_user: false\n"
        "brief_format: v1\n"
        "brief_source_kind: brief_interview\n"
        "brief_status: draft\n"
        "title: Project Brief\n"
        "---\n\n"
        "# Project Brief\n\n"
        "## What does the product do?\n"
        "- Manage customer assignments.\n",
        encoding="utf-8",
    )
    confirmed = tmp_path / "confirmed-brief.md"
    result = runner.invoke(
        app,
        [
            "brief",
            "confirm",
            "--input",
            str(draft),
            "--output",
            str(confirmed),
        ],
    )

    assert result.exit_code == 0, result.output
    text = confirmed.read_text(encoding="utf-8")
    metadata, body = split_brief_text(text)
    assert metadata["brief_status"] == "confirmed"
    assert metadata["brief_confirmed_by_user"] is True
    assert metadata["brief_source_kind"] == "brief_interview"
    assert body.startswith("# Project Brief")
    assert is_confirmed_brief_text(text)


def test_brief_confirm_dry_run_prints_confirmed_brief(tmp_path: Path) -> None:
    draft = tmp_path / "draft-brief.md"
    draft.write_text(
        "---\n"
        "brief_confirmed_by_user: false\n"
        "brief_format: v1\n"
        "brief_source_kind: brief_interview\n"
        "brief_status: draft\n"
        "title: Project Brief\n"
        "---\n\n"
        "# Project Brief\n\n"
        "## What does the product do?\n"
        "- Manage customer assignments.\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "brief",
            "confirm",
            "--input",
            str(draft),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "brief_status: confirmed" in result.output
    assert "Dry run: brief was not written to disk." in result.output
