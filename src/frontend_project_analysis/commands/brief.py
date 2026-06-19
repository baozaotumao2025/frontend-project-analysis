"""Brief collection commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer

from ..core.config import get_settings
from ..llm import run_brief_assistant
from ..schemas import BriefAssistantPayload
from .utils import handle_service_error

brief_app = typer.Typer(
    help="Brief collection and interview commands, with optional LLM assistance."
)


@dataclass(frozen=True)
class PromptStep:
    key: str
    prompt: str
    follow_up: str | None = None
    signal_terms: tuple[str, ...] = ()


def register_brief_commands(app: typer.Typer) -> None:
    app.add_typer(brief_app, name="brief")


def _normalize_answer(value: str) -> str:
    answer = value.strip()
    return answer if answer else "unknown"


def _has_enough_detail(answer: str) -> bool:
    normalized = answer.strip().lower()
    if not normalized or normalized == "unknown":
        return False
    if len(normalized) < 18:
        return False
    return any(char.isalpha() for char in normalized)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _build_brief_markdown(
    answers: dict[str, str],
    *,
    assistant_followups: list[tuple[str, str]] | None = None,
    assistant_notes: BriefAssistantPayload | None = None,
) -> str:
    lines = [
        "# Project Brief",
        "",
        "## What does the product do?",
        answers["what"],
        "",
        "## Who are the main users?",
        answers["who"],
        "",
        "## What are the core usage scenarios?",
        answers["scenarios"],
        "",
        "## What should stay invisible or restricted?",
        answers["invisible"],
        "",
        "## What constraints or dependencies matter most?",
        answers["constraints"],
        "",
        "## What evidence supports this brief?",
        answers["evidence"],
        "",
        "## What are the biggest risks or assumptions?",
        answers["risk"],
        "",
        "## What accessibility expectations matter?",
        answers["accessibility"],
        "",
        "## What should we observe after release?",
        answers["observability"],
        "",
        "## What release or compliance constraints matter?",
        answers["release"],
        "",
    ]
    if assistant_followups:
        lines.extend(["## AI Assistant Follow-Ups", ""])
        for index, (question, answer) in enumerate(assistant_followups, start=1):
            lines.extend([f"### {index}. {question}", "", answer, ""])
    if assistant_notes is not None:
        lines.extend(
            [
                "## AI Assistant Summary",
                "",
                assistant_notes.summary,
                "",
                "## AI Assistant Gaps",
                "",
                *([f"- {gap}" for gap in assistant_notes.gaps] or ["- none"]),
                "",
                "## AI Assistant Recommendations",
                "",
                *(
                    [f"- {question}" for question in assistant_notes.recommended_questions]
                    or ["- none"]
                ),
                "",
            ]
        )
        if assistant_notes.draft_brief:
            lines.extend(
                [
                    "## AI Assistant Draft Brief",
                    "",
                    assistant_notes.draft_brief,
                    "",
                ]
            )
    return "\n".join(lines)


def _build_transcript_markdown(transcript: list[tuple[str, str]]) -> str:
    lines = ["# Brief Interview Transcript", ""]
    for index, (prompt, answer) in enumerate(transcript, start=1):
        lines.extend(
            [
                f"## {index}. {prompt}",
                "",
                answer,
                "",
            ]
        )
    return "\n".join(lines)


def _build_brief_assistant_packet(
    answers: dict[str, str],
    transcript: list[tuple[str, str]],
    remaining_budget: int,
    *,
    stage: str,
) -> dict:
    return {
        "stage": stage,
        "answers": answers,
        "transcript": transcript,
        "remaining_budget": remaining_budget,
    }


def _ask(prompt: str) -> str:
    return _normalize_answer(typer.prompt(prompt))


def _ask_recorded(prompt: str, transcript: list[tuple[str, str]] | None) -> str:
    answer = _ask(prompt)
    if transcript is not None:
        transcript.append((prompt, answer))
    return answer


def _collect_core_answers(
    max_questions: int,
    transcript: list[tuple[str, str]] | None,
) -> tuple[dict[str, str], int]:
    steps = [
        PromptStep(
            key="what",
            prompt="1/3 What does the product do?",
            follow_up="What is the main outcome the product should help users achieve?",
            signal_terms=("product", "platform", "tool", "system", "workflow"),
        ),
        PromptStep(
            key="who",
            prompt="2/3 Who are the main users?",
            follow_up="Which role should we treat as the primary Persona first?",
            signal_terms=("user", "role", "persona", "team", "admin", "sales", "ops"),
        ),
        PromptStep(
            key="scenarios",
            prompt="3/3 What are the core usage scenarios?",
            follow_up="What is the first end-to-end workflow users must complete?",
            signal_terms=("workflow", "scenario", "flow", "process", "task"),
        ),
    ]
    answers: dict[str, str] = {}
    questions_asked = 0
    for step in steps:
        if questions_asked >= max_questions:
            break
        answers[step.key] = _ask_recorded(step.prompt, transcript)
        questions_asked += 1

    follow_up_steps = [
        step for step in steps if step.key in answers and not _has_enough_detail(answers[step.key])
    ]
    if not follow_up_steps:
        return answers, questions_asked

    typer.echo("A few details are still unclear, so I am narrowing in on them.")
    for step in follow_up_steps:
        if questions_asked >= max_questions:
            break
        if step.follow_up is None:
            continue
        refined = _ask_recorded(step.follow_up, transcript)
        questions_asked += 1
        if _has_enough_detail(refined):
            answers[step.key] = refined
    return answers, questions_asked


def _collect_targeted_followups(
    answers: dict[str, str],
    max_questions: int,
    transcript: list[tuple[str, str]] | None,
) -> tuple[dict[str, str], int]:
    candidates: list[PromptStep] = []
    joined = " ".join(answers.values())

    if _contains_any(
        joined, ("admin", "permission", "restricted", "role", "billing", "auth", "access")
    ):
        candidates.append(
            PromptStep(
                key="invisible",
                prompt="What should stay invisible or restricted?",
            )
        )

    if _contains_any(
        joined, ("api", "integration", "dependency", "sync", "import", "export", "data", "database")
    ):
        candidates.append(
            PromptStep(
                key="constraints",
                prompt="What constraints or dependencies matter most?",
            )
        )

    answers_out: dict[str, str] = {}
    if not candidates:
        answers_out["invisible"] = "unknown"
        answers_out["constraints"] = "unknown"
        return answers_out, 0

    questions_asked = 0
    for step in candidates:
        if questions_asked >= max_questions:
            break
        answer = _ask_recorded(step.prompt, transcript)
        questions_asked += 1
        answers_out[step.key] = answer if _has_enough_detail(answer) else "unknown"
    if "invisible" not in answers_out:
        answers_out["invisible"] = "unknown"
    if "constraints" not in answers_out:
        answers_out["constraints"] = "unknown"
    return answers_out, questions_asked


def _collect_cross_cutting_followups(
    max_questions: int,
    transcript: list[tuple[str, str]] | None,
) -> tuple[dict[str, str], int]:
    steps = [
        PromptStep(
            key="evidence",
            prompt="What evidence supports this brief?",
        ),
        PromptStep(
            key="risk",
            prompt="What are the biggest risks or assumptions?",
        ),
        PromptStep(
            key="accessibility",
            prompt="What accessibility expectations matter?",
        ),
        PromptStep(
            key="observability",
            prompt="What should we observe after release?",
        ),
        PromptStep(
            key="release",
            prompt="What release or compliance constraints matter?",
        ),
    ]
    answers_out: dict[str, str] = {}
    questions_asked = 0
    for step in steps:
        if questions_asked >= max_questions:
            break
        answer = _ask_recorded(step.prompt, transcript)
        questions_asked += 1
        answers_out[step.key] = answer if _has_enough_detail(answer) else "unknown"
    for step in steps:
        answers_out.setdefault(step.key, "unknown")
    return answers_out, questions_asked


def _collect_ai_followups(
    answers: dict[str, str],
    remaining_budget: int,
    transcript: list[tuple[str, str]] | None,
) -> tuple[list[tuple[str, str]], BriefAssistantPayload | None, int]:
    if transcript is None or remaining_budget <= 0:
        return [], None, 0
    settings = get_settings()
    packet = _build_brief_assistant_packet(answers, transcript, remaining_budget, stage="followup")
    assistant_response = run_brief_assistant(packet, settings, stage="followup")
    assistant = assistant_response.payload
    followups: list[tuple[str, str]] = []
    questions = [
        question.strip()
        for question in assistant.recommended_questions
        if question.strip()
    ]
    if not questions:
        return followups, assistant, 0
    typer.echo("AI assistant suggested the following follow-up questions:")
    for question in questions[:remaining_budget]:
        typer.echo(f"- {question}")
        answer = _ask_recorded(question, transcript)
        followups.append((question, answer))
    return followups, assistant, len(followups)


def _collect_ai_summary(
    answers: dict[str, str],
    transcript: list[tuple[str, str]] | None,
) -> BriefAssistantPayload | None:
    if transcript is None:
        return None
    settings = get_settings()
    packet = _build_brief_assistant_packet(answers, transcript, 0, stage="summary")
    assistant_response = run_brief_assistant(packet, settings, stage="summary")
    return assistant_response.payload


@brief_app.command("interview")
@handle_service_error
def brief_interview(
    output: Path = typer.Option(..., "--output"),
    force: bool = typer.Option(False, "--force"),
    max_questions: int = typer.Option(8, "--max-questions", min=3),
    dry_run: bool = typer.Option(False, "--dry-run"),
    transcript: Path | None = typer.Option(None, "--transcript"),
    llm_assist: bool = typer.Option(False, "--llm-assist/--no-llm-assist"),
) -> None:
    if output.exists() and not force:
        raise typer.BadParameter(f"{output} already exists. Use --force to overwrite it.")

    if max_questions < 3:
        raise typer.BadParameter("--max-questions must be at least 3.")
    if transcript is not None and transcript.exists() and not force:
        raise typer.BadParameter(f"{transcript} already exists. Use --force to overwrite it.")

    typer.echo(
        "Answer the following questions. The interview stops as soon as the brief is clear enough."
    )
    question_transcript: list[tuple[str, str]] = []
    answers, questions_asked = _collect_core_answers(max_questions, question_transcript)
    remaining_budget = max_questions - questions_asked
    assistant_followups: list[tuple[str, str]] = []
    assistant_notes: BriefAssistantPayload | None = None
    if llm_assist and remaining_budget > 0:
        ai_followups, assistant_notes, ai_questions = _collect_ai_followups(
            answers,
            remaining_budget,
            question_transcript,
        )
        assistant_followups.extend(ai_followups)
        questions_asked += ai_questions
        remaining_budget = max_questions - questions_asked
    if remaining_budget > 0:
        followup_answers, followup_questions = _collect_targeted_followups(
            answers,
            remaining_budget,
            question_transcript,
        )
        answers.update(followup_answers)
        questions_asked += followup_questions
    else:
        answers.setdefault("invisible", "unknown")
        answers.setdefault("constraints", "unknown")

    remaining_budget = max_questions - questions_asked
    if remaining_budget > 0:
        cross_cutting_answers, cross_cutting_questions = _collect_cross_cutting_followups(
            remaining_budget,
            question_transcript,
        )
        answers.update(cross_cutting_answers)
        questions_asked += cross_cutting_questions

    if llm_assist:
        assistant_notes = _collect_ai_summary(answers, question_transcript)
        if assistant_notes is not None and not assistant_notes.recommended_questions:
            assistant_notes = assistant_notes.model_copy(
                update={
                    "recommended_questions": [question for question, _ in assistant_followups]
                }
            )

    for key in (
        "invisible",
        "constraints",
        "evidence",
        "risk",
        "accessibility",
        "observability",
        "release",
    ):
        answers.setdefault(key, "unknown")

    markdown = _build_brief_markdown(
        answers,
        assistant_followups=assistant_followups,
        assistant_notes=assistant_notes,
    )
    transcript_markdown = _build_transcript_markdown(question_transcript)
    if dry_run:
        typer.echo(markdown)
        if transcript is not None:
            typer.echo(transcript_markdown)
        typer.echo("Dry run: brief was not written to disk.")
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    if transcript is not None:
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text(transcript_markdown, encoding="utf-8")
    typer.echo(f"Wrote brief to {output}")
    if transcript is not None:
        typer.echo(f"Wrote transcript to {transcript}")


@brief_app.command("assistant")
@handle_service_error
def brief_assistant(
    output: Path = typer.Option(..., "--output"),
    force: bool = typer.Option(False, "--force"),
    max_questions: int = typer.Option(8, "--max-questions", min=3),
    dry_run: bool = typer.Option(False, "--dry-run"),
    transcript: Path | None = typer.Option(None, "--transcript"),
) -> None:
    brief_interview(
        output=output,
        force=force,
        max_questions=max_questions,
        dry_run=dry_run,
        transcript=transcript,
        llm_assist=True,
    )
