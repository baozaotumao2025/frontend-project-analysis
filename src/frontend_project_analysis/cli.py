"""Typer CLI for workflow governance."""

from __future__ import annotations

import json

import typer

from .commands import (
    register_artifact_commands,
    register_db_commands,
    register_export_commands,
    register_import_commands,
    register_project_commands,
    register_review_commands,
    register_workflow_commands,
)
from .commands.project import _render_install_payload, _run_project_init
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
register_artifact_commands(app)
register_review_commands(app)
register_export_commands(app)
register_import_commands(app)
register_db_commands(app)
register_workflow_commands(app)


@app.command("install")
def install(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    payload = _render_install_payload(force=force, dry_run=dry_run)
    typer.echo(json.dumps(payload, indent=2))


@app.command("init")
def init(
    project: str = typer.Option(..., "--project"),
    name: str = typer.Option(..., "--name"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    install_payload = _render_install_payload(force=force, dry_run=dry_run)
    init_payload = _run_project_init(project=project, name=name, force=force, dry_run=dry_run)
    typer.echo(
        json.dumps(
            {
                "command": "init",
                "force": force,
                "dry_run": dry_run,
                "install": install_payload,
                "project": init_payload,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
