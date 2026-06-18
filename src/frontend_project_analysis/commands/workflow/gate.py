"""Workflow round gate commands."""

from __future__ import annotations

import typer

from ...core.config import get_paths
from ...infrastructure.storage import session_scope
from ...repositories.projects import get_project
from ...workflow.round_gates import assert_round_gate
from ..utils import handle_service_error
from . import workflow_app


@workflow_app.command("gate")
@handle_service_error
def workflow_gate(
    project: str = typer.Option(..., "--project"),
    round_number: int = typer.Option(..., "--round"),
) -> None:
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        result = assert_round_gate(session, project_row, round_number)
    if result.passed:
        if result.input_type is None:
            typer.echo(f"Round {round_number} has no upstream gate.")
        else:
            typer.echo(
                f"Round {round_number} gate passed for project {project}: "
                f"{result.checked_count} {result.input_type.value} revision(s) approved."
            )
