"""Workflow round gate commands."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...core.domain import WorkflowMode
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.round_gates import assert_round_gate
from ..utils import handle_service_error
from . import explore_workflow_app, workflow_app


def _emit_gate_message(project: str, round_number: int, result) -> None:
    if result.input_type is None:
        typer.echo(f"Round {round_number} has no upstream gate.")
        return

    if result.mode == WorkflowMode.EXPLORE:
        blocked = (
            f" with {len(result.blocked_refs)} unapproved upstream revision(s)"
            if result.blocked_refs
            else ""
        )
        typer.echo(
            f"Round {round_number} explore gate passed for project {project}{blocked}: "
            f"{result.checked_count} {result.input_type.value} revision(s) available."
        )
        return

    typer.echo(
        f"Round {round_number} gate passed for project {project}: "
        f"{result.checked_count} {result.input_type.value} revision(s) approved."
    )


def _emit_start_message(project: str, round_number: int, result) -> None:
    if result.input_type is None:
        typer.echo(f"Round {round_number} is ready to start for project {project}.")
        return

    if result.mode == WorkflowMode.EXPLORE:
        blocked = (
            f" including {len(result.blocked_refs)} unapproved upstream revision(s)"
            if result.blocked_refs
            else ""
        )
        typer.echo(
            f"Round {round_number} is ready to explore for project {project}{blocked}: "
            f"{result.checked_count} {result.input_type.value} revision(s) available."
        )
        return

    typer.echo(
        f"Round {round_number} is ready to start for project {project}: "
        f"{result.checked_count} {result.input_type.value} revision(s) approved."
    )


@workflow_app.command("gate")
@handle_service_error
def workflow_gate(
    project: str = typer.Option(..., "--project"),
    round_number: int = typer.Option(..., "--round"),
    mode: WorkflowMode = typer.Option(WorkflowMode.FORMAL, "--mode"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        result = assert_round_gate(session, project_row, round_number, mode=mode)
    if result.passed:
        _emit_gate_message(project, round_number, result)


@workflow_app.command("start")
@handle_service_error
def workflow_start(
    project: str = typer.Option(..., "--project"),
    round_number: int = typer.Option(..., "--round"),
    mode: WorkflowMode = typer.Option(WorkflowMode.FORMAL, "--mode"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        result = assert_round_gate(session, project_row, round_number, mode=mode)

    if result.input_type is None:
        _emit_start_message(project, round_number, result)
        return

    _emit_start_message(project, round_number, result)


@explore_workflow_app.command("gate")
@handle_service_error
def workflow_explore_gate(
    project: str = typer.Option(..., "--project"),
    round_number: int = typer.Option(..., "--round"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        result = assert_round_gate(session, project_row, round_number, mode=WorkflowMode.EXPLORE)
    if result.passed:
        _emit_gate_message(project, round_number, result)


@explore_workflow_app.command("start")
@handle_service_error
def workflow_explore_start(
    project: str = typer.Option(..., "--project"),
    round_number: int = typer.Option(..., "--round"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        result = assert_round_gate(session, project_row, round_number, mode=WorkflowMode.EXPLORE)

    _emit_start_message(project, round_number, result)
