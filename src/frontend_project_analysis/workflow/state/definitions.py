"""Shared workflow state definitions."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.errors import AppError


class WorkflowStateError(AppError):
    """Raised when workflow state operations fail validation."""


@dataclass
class CheckFinding:
    severity: str
    code: str
    message: str
    artifact_ref: str | None = None

