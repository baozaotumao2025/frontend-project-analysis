"""Project command group."""

from __future__ import annotations

import json

import typer

from ..core.config import get_paths
from ..infrastructure.storage import initialize_database, session_scope, wipe_database
from ..repositories.projects import ensure_project
from ..workflow.io import initialize_project, install_project_scaffold
from .utils import handle_service_error

project_app = typer.Typer(help="Project lifecycle commands.")


def register_project_commands(app: typer.Typer) -> None:
    app.add_typer(project_app, name="project")


def _render_install_payload(*, force: bool, dry_run: bool) -> dict[str, object]:
    paths = get_paths()
    actions = install_project_scaffold(paths.root, force=force, dry_run=dry_run)
    return {
        "command": "install",
        "force": force,
        "dry_run": dry_run,
        "root": str(paths.root),
        "actions": actions,
    }


def _run_project_init(
    *,
    project: str,
    name: str,
    force: bool,
    dry_run: bool,
) -> dict[str, object]:
    paths = get_paths()
    if dry_run:
        return {
            "command": "project-init",
            "force": force,
            "dry_run": True,
            "project_key": project,
            "project_name": name,
            "root": str(paths.root),
            "state_dir": str(paths.state_dir),
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
                    "path": "docs/ and specs/ scaffold",
                    "action": "ensure_project_document_layout",
                },
            ],
        }

    if force and paths.db_path.exists():
        wipe_database(paths)
    initialize_database(paths)
    payload = initialize_project(paths, project, name)
    with session_scope(paths) as session:
        ensure_project(session, project, name, paths.root)
        session.commit()
    payload.update(
        {
            "command": "project-init",
            "force": force,
            "dry_run": False,
        }
    )
    return payload


@project_app.command("install")
@handle_service_error
def project_install(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    payload = _render_install_payload(force=force, dry_run=dry_run)
    typer.echo(json.dumps(payload, indent=2))


@project_app.command("init")
@handle_service_error
def project_init(
    project: str = typer.Option(..., "--project"),
    name: str = typer.Option(..., "--name"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    payload = _run_project_init(project=project, name=name, force=force, dry_run=dry_run)
    typer.echo(json.dumps(payload, indent=2))

