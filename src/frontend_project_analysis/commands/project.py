"""Project command group."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ..core.config import get_paths
from ..infrastructure.storage import initialize_database, session_scope, wipe_database
from ..repositories.projects import ensure_project
from ..workflow.io import initialize_project
from .utils import handle_service_error

project_app = typer.Typer(help="Project lifecycle commands.")


def register_project_commands(app: typer.Typer) -> None:
    app.add_typer(project_app, name="project")


def _run_project_init(
    *,
    project: str,
    name: str,
    brief: str | None,
    brief_file: Path | None,
    force: bool,
    dry_run: bool,
) -> dict[str, object]:
    paths = get_paths()
    if brief is not None and brief_file is not None:
        raise typer.BadParameter("Use either --brief or --brief-file, not both.")
    if brief is None and brief_file is None:
        raise typer.BadParameter("Provide either --brief or --brief-file.")
    brief_text = brief
    brief_source = None
    if brief_file is not None:
        brief_source = brief_file
        brief_text = brief_file.read_text(encoding="utf-8")
    elif brief_text is not None:
        brief_source = "<inline>"
    if dry_run:
        return {
            "command": "project-init",
            "force": force,
            "dry_run": True,
            "project_key": project,
            "project_name": name,
            "root": str(paths.root),
            "state_dir": str(paths.state_dir),
            "analysis_dir": str(paths.root / "analysis"),
            "database": "would_reset" if force and paths.db_path.exists() else "would_initialize",
            "actions": [
                {
                    "path": str(paths.db_path),
                    "action": "reset" if force and paths.db_path.exists() else "create_or_migrate",
                },
                {
                    "path": str(paths.state_dir),
                    "action": "ensure_state_dirs",
                },
                {
                    "path": "analysis/",
                    "action": "ensure_analysis_workspace",
                },
                {
                    "path": "analysis/brief.md",
                    "action": "write_brief_from_input",
                    "source": str(brief_source) if brief_source else None,
                },
            ],
            "brief_source": str(brief_source) if brief_source else None,
        }

    if force and paths.db_path.exists():
        wipe_database(paths)
    initialize_database(paths)
    payload = initialize_project(paths, project, name, brief_text=brief_text)
    with session_scope(paths) as session:
        ensure_project(session, project, name, paths.root)
        session.commit()
    payload.update(
        {
            "command": "project-init",
            "force": force,
            "dry_run": False,
            "brief_source": str(brief_source) if brief_source else None,
        }
    )
    return payload


@project_app.command("init")
@handle_service_error
def project_init(
    project: str = typer.Option(..., "--project"),
    name: str = typer.Option(..., "--name"),
    brief: str | None = typer.Option(None, "--brief"),
    brief_file: Path | None = typer.Option(None, "--brief-file", exists=True, dir_okay=False),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    payload = _run_project_init(
        project=project,
        name=name,
        brief=brief,
        brief_file=brief_file,
        force=force,
        dry_run=dry_run,
    )
    typer.echo(json.dumps(payload, indent=2))
