"""Database command group."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import typer
from sqlalchemy import delete

from .repositories import get_project
from .storage import (
    backup_database,
    get_migration_status,
    initialize_database,
    restore_database,
    session_scope,
    wipe_database,
)

db_app = typer.Typer(help="Database maintenance commands.")


def register_db_commands(app: typer.Typer) -> None:
    app.add_typer(db_app, name="db")


@db_app.command("init")
def db_init() -> None:
    from .config import get_paths

    paths = get_paths()
    db_path = initialize_database(paths)
    typer.echo(f"Initialized database at {db_path}")


@db_app.command("check")
def db_check() -> None:
    from .config import get_paths

    paths = get_paths()
    status = get_migration_status(paths)
    if not status.is_initialized:
        typer.secho("Database is not initialized.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    findings: list[str] = []
    with sqlite3.connect(paths.db_path) as connection:
        fk_findings = connection.execute("PRAGMA foreign_key_check").fetchall()
    if status.current_revision != status.head_revision:
        findings.append(
            "Migration mismatch: "
            f"current={status.current_revision or 'none'}, head={status.head_revision or 'none'}."
        )
    if fk_findings:
        findings.append(f"Foreign key violations detected: {fk_findings}")
    if findings:
        for finding in findings:
            typer.secho(finding, fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    typer.echo(f"Database check passed for {paths.db_path}")


@db_app.command("migrate")
def db_migrate() -> None:
    from .config import get_paths

    paths = get_paths()
    initialize_database(paths)
    typer.echo(f"Applied migrations to {paths.db_path}")


@db_app.command("backup")
def db_backup(output: Path | None = typer.Option(None, "--output")) -> None:
    from .config import get_paths

    backup_path = backup_database(get_paths(), output)
    typer.echo(f"Backup written to {backup_path}")


@db_app.command("restore")
def db_restore(source: Path = typer.Option(..., "--from")) -> None:
    from .config import get_paths

    previous, current = restore_database(get_paths(), source)
    typer.echo(f"Restored database to {current}")
    typer.echo(f"Previous database snapshot: {previous}")


@db_app.command("wipe")
def db_wipe(yes: bool = typer.Option(False, "--yes", help="Confirm destructive wipe.")) -> None:
    from .config import get_paths

    if not yes:
        typer.secho("Refusing to wipe database without --yes.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    wipe_database(get_paths())
    typer.echo("Database file removed.")


@db_app.command("reset-project")
def db_reset_project(
    project: str = typer.Option(..., "--project"),
    yes: bool = typer.Option(False, "--yes", help="Confirm project data reset."),
) -> None:
    from .config import get_paths

    if not yes:
        typer.secho("Refusing to reset project without --yes.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    with session_scope(get_paths()) as session:
        project_row = get_project(session, project)
        session.execute(
            delete(project_row.__class__).where(project_row.__class__.id == project_row.id)
        )
        session.commit()
    typer.echo(f"Reset project '{project}' data.")
