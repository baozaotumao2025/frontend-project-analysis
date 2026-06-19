"""Review command group."""

from __future__ import annotations

import typer

review_app = typer.Typer(help="Structural and semantic review commands.")


def register_review_commands(app: typer.Typer) -> None:
    app.add_typer(review_app, name="review")


from . import (  # noqa: E402,F401
    lifecycle,
    semantic_packet,
    semantic_record,
    semantic_run,
    resubmit,
    structural,
)
