"""Typer CLI for workflow governance."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .commands import (
    register_artifact_commands,
    register_brief_commands,
    register_db_commands,
    register_export_commands,
    register_import_commands,
    register_project_commands,
    register_review_commands,
    register_workflow_commands,
)
from .commands.project import _run_project_init
from .core.config import get_paths, get_settings
from .infrastructure.logging_utils import configure_logging, get_logger

app = typer.Typer(help="Frontend project analysis workflow infrastructure.")
logger = get_logger(__name__)


@app.callback()
def main() -> None:
    """Bootstrap shared runtime configuration."""

    settings = get_settings()
    paths = get_paths()
    configure_logging(settings, paths)
    logger.debug("Runtime initialized with state dir %s", paths.state_dir)


register_project_commands(app)
register_brief_commands(app)
register_artifact_commands(app)
register_review_commands(app)
register_export_commands(app)
register_import_commands(app)
register_db_commands(app)
register_workflow_commands(app)


@app.command("init")
def init(
    project: str = typer.Option(..., "--project"),
    name: str = typer.Option(..., "--name"),
    brief: str | None = typer.Option(None, "--brief"),
    brief_file: Path | None = typer.Option(None, "--brief-file", exists=True, dir_okay=False),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    init_payload = _run_project_init(
        project=project,
        name=name,
        brief=brief,
        brief_file=brief_file,
        force=force,
        dry_run=dry_run,
    )
    typer.echo(
        json.dumps(
            {
                "command": "init",
                "force": force,
                "dry_run": dry_run,
                "project": init_payload,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
