"""Shared CLI command helpers."""

from __future__ import annotations

from functools import wraps

import typer
from pydantic import ValidationError

from ..core.errors import AppError, ConfigurationError
from ..workflow.state import WorkflowStateError as ServiceError


def handle_service_error(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except typer.Exit:
            raise
        except (AppError, ServiceError, ConfigurationError, ValidationError) as exc:
            from ..infrastructure.logging_utils import get_logger

            logger = get_logger(__name__)
            logger.error("Command failed: %s", exc)
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc
        except Exception as exc:  # pragma: no cover - defensive path
            from ..infrastructure.logging_utils import get_logger

            logger = get_logger(__name__)
            logger.exception("Unhandled exception")
            typer.secho(
                f"Unexpected error: {exc}. Check the log file for details.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1) from exc

    return wrapper
