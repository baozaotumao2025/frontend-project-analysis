"""Repository-level exceptions."""

from __future__ import annotations

from ..core.errors import AppError


class RepositoryError(AppError):
    """Raised when repository-level workflow operations fail."""

