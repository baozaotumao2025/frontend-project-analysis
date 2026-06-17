"""Path and environment helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigurationError

STATE_DIR_NAME = ".frontend-project-analysis"


class Settings(BaseSettings):
    """Application settings loaded from environment and `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FPA_",
        extra="ignore",
    )

    root_dir: str | None = None
    state_dir: str | None = None
    db_path: str | None = None
    backup_dir: str | None = None
    export_dir: str | None = None
    log_dir: str | None = None
    audit_dir: str | None = None

    log_level: str = "INFO"
    log_to_stderr: bool = True
    log_file_name: str = "app.log"
    log_json: bool = False

    llm_provider: str = "openai"
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_api_path: str = "/responses"
    llm_timeout_seconds: int = 60
    llm_max_output_tokens: int = 1200
    llm_max_retries: int = 3
    llm_retry_initial_backoff_seconds: float = 1.0
    llm_retry_max_backoff_seconds: float = 8.0
    llm_temperature: float = 0
    llm_organization: str | None = None
    anthropic_version: str = "2023-06-01"

    semantic_review_auto_approve: bool = False
    semantic_review_output_name: str = Field(
        default="semantic-review-packet.json",
    )


_SETTINGS: Settings | None = None


@dataclass(frozen=True)
class AppPaths:
    root: Path
    state_dir: Path
    db_path: Path
    backup_dir: Path
    export_dir: Path
    log_dir: Path
    audit_dir: Path


def resolve_root(root: Path | None = None) -> Path:
    if root is not None:
        return root.resolve()
    return Path.cwd().resolve()


def get_settings(refresh: bool = False) -> Settings:
    global _SETTINGS
    if _SETTINGS is None or refresh:
        _SETTINGS = Settings()
    return _SETTINGS


def reset_settings_cache() -> None:
    global _SETTINGS
    _SETTINGS = None


def require_llm_settings(settings: Settings | None = None) -> Settings:
    resolved = settings or get_settings()
    if not resolved.llm_provider:
        raise ConfigurationError("FPA_LLM_PROVIDER is required for semantic review.")
    return resolved


def get_paths(root: Path | None = None) -> AppPaths:
    settings = get_settings()
    repo_root = resolve_root(Path(settings.root_dir).expanduser() if settings.root_dir else root)
    state_dir = (
        Path(settings.state_dir).expanduser().resolve()
        if settings.state_dir
        else repo_root / STATE_DIR_NAME
    )
    db_path = (
        Path(settings.db_path).expanduser().resolve()
        if settings.db_path
        else state_dir / "state.db"
    )
    backup_dir = (
        Path(settings.backup_dir).expanduser().resolve()
        if settings.backup_dir
        else state_dir / "backups"
    )
    export_dir = (
        Path(settings.export_dir).expanduser().resolve()
        if settings.export_dir
        else state_dir / "exports"
    )
    log_dir = (
        Path(settings.log_dir).expanduser().resolve()
        if settings.log_dir
        else state_dir / "logs"
    )
    audit_dir = (
        Path(settings.audit_dir).expanduser().resolve()
        if settings.audit_dir
        else state_dir / "audits"
    )
    return AppPaths(
        root=repo_root,
        state_dir=state_dir,
        db_path=db_path,
        backup_dir=backup_dir,
        export_dir=export_dir,
        log_dir=log_dir,
        audit_dir=audit_dir,
    )


def ensure_state_dirs(paths: AppPaths) -> None:
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    paths.export_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    paths.audit_dir.mkdir(parents=True, exist_ok=True)
