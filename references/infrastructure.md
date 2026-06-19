# Infrastructure

## Goal

This skill ships with a Python workflow backend so that relationship storage and project iteration can be managed consistently across projects.

## Runtime

- Package manager: `uv`
- Python version: `3.12`
- CLI entrypoint: `uv run fpa ...`
- Configuration source: `.env`
- Database migrations: `Alembic`

## Architecture

The Python code follows a layered split:

- `core/`: enums, review rubrics, stable business rules, and runtime configuration
- `infrastructure/`: logging, document parsing, SQLite session helpers, and Alembic lifecycle
- `models/`: ORM definitions and compatibility exports
- `schemas/`: workflow and provider payload models
- `repositories/`: persistence helpers split into `projects`, `dependencies`, `versions`, and `reviews`
- `workflow/`: state checks, transitions, semantic packet construction, and IO facade
- `workflow/state/`: shared workflow state definitions, ready checks, gate checks, structural review, and transitions
- `workflow/io/`: audit file archiving, JSON export, manifest export, relations export, Markdown import, and manifest import helpers
- `llm/`: provider routing, request builders, validation, provider helpers, and shared response types
- `llm/providers/`: provider-specific adapters
- `llm/transport/`: HTTP transport, error mapping, and backoff helpers
- `commands/`: CLI subcommand registration and command handlers, with `commands/artifact/`, `commands/review/`, `commands/db/`, `commands/export/`, and `commands/imports/` split by scenario; `commands/utils.py` keeps shared decorators
- `cli`: thin command entrypoint that only wires subcommands together

This keeps structural validation deterministic and keeps provider-specific code isolated from the workflow rules.

## Observability

- Text logs are available by default.
- `FPA_LOG_JSON=true` switches the runtime to structured JSON logs.
- Trace and request identifiers flow through logs, provider audits, and audit file names.
- Provider audit timelines are stored as event arrays so each call can be replayed step by step.

## State Model

Each target project keeps its workflow state inside:

```text
.frontend-project-analysis/
  state.db
  backups/
  exports/
  logs/
  audits/
```

- `state.db`: SQLite source of truth
- `backups/`: timestamped database backups
- `exports/`: JSON manifests and exported relation files
- `logs/`: reserved for future automation logs
- `audits/`: provider request/response archives and event timelines
- `init` ensures this directory is listed in the calling project's `.gitignore`

## Source Of Truth

- SQLite stores authoritative structure:
  - project registry
  - artifact identity
  - dependency graph
  - review records
  - transition history
- Markdown files remain the human-readable projection layer
- Matrix files should be exported from the database instead of edited by hand

## Core Tables

- `projects`
- `artifacts`
- `artifact_versions`
- `artifact_dependencies`
- `artifact_reviews`
- `artifact_review_findings`
- `artifact_transitions`
- `provider_call_audits` with `events_json` storing the provider event timeline

## Review Integration

Structural review and semantic review are part of the runtime backend, but their lifecycle semantics are defined in [references/state-machine.md](state-machine.md) and their round-by-round contract is defined in [references/workflow.md](workflow.md).

Structural review is code-driven and deterministic.

Semantic review is host-first and optionally external-LLM-assisted.
When `FPA_LLM_PROVIDER=host`, the CLI emits the review packet and lets the current Codex or Claude Code session make the semantic judgment instead of the repository code calling an external API.

The backend prepares a structured review packet containing:

- artifact identity
- upstream and downstream references
- current metadata and body snapshot
- a rubric tailored to the artifact type

The LLM should return structured JSON so the result can be recorded without weakening consistency controls.
In `host` mode, the structured packet is handed to the current host agent, which automatically produces the judgment, and the result is recorded with `review semantic-record`.

## Database Maintenance

Supported workflows:

- `uv run fpa install`
- `uv run fpa init --project ... --name ...`
- `uv run fpa db init`
- `uv run fpa db backup`
- `uv run fpa db restore --from ...`
- `uv run fpa db wipe --yes`

Database migrations are applied automatically when the CLI opens a session or initializes the database.
The migration layer resolves the repository root `alembic.ini`, points Alembic at `migrations/`,
and prepends `src/` so `frontend_project_analysis` can be imported during migration runs.
This is the same wiring `install` and `init` rely on when bootstrapping a fresh target project.

## Import And Export

- `uv run fpa import markdown-scan --project <key>`
- `uv run fpa import markdown-scan --project <key> --apply`
- `uv run fpa export manifest --project <key>`
- `uv run fpa export relations --project <key>`

When `markdown-scan --apply` runs, the importer refreshes the document indexes and relation matrices from the current SQLite state.

## Skill Integration Rule

When the skill needs workflow state, it should call CLI commands instead of inferring graph consistency from Markdown alone.

## Environment Configuration

Use `.env` for runtime configuration so the same skill can target different providers and project layouts without code edits.
If no external model is configured, set `FPA_LLM_PROVIDER=host` and let the current Codex or Claude Code session make the semantic judgment from the emitted packet.

Recommended keys:

- `FPA_LLM_PROVIDER`
- `FPA_LLM_MODEL`
- `FPA_LLM_BASE_URL`
- `FPA_LLM_API_KEY`
- `FPA_LLM_API_PATH`
- `FPA_LLM_MAX_RETRIES`
- `FPA_LLM_RETRY_INITIAL_BACKOFF_SECONDS`
- `FPA_LLM_RETRY_MAX_BACKOFF_SECONDS`
- `FPA_STATE_DIR`
- `FPA_DB_PATH`
- `FPA_EXPORT_DIR`
- `FPA_LOG_DIR`
- `FPA_AUDIT_DIR`
- `FPA_LOG_LEVEL`
