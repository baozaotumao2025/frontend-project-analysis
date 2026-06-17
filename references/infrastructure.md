# Infrastructure

## Goal

This skill ships with a Python workflow backend so that relationship storage, review state, and project iteration can be managed consistently across projects.

## Runtime

- Package manager: `uv`
- Python version: `3.12`
- CLI entrypoint: `uv run fpa ...`
- Configuration source: `.env`
- Database migrations: `Alembic`

## Architecture

The Python code follows a layered split:

- `domain`: enums, review rubrics, and stable business rules
- `schemas`: typed payloads for packets, provider responses, and audits
- `repositories`: compatibility facade for persistence helpers
- `repository_artifacts`: project, artifact, version, dependency, and graph checks
- `repository_reviews`: review and provider-audit persistence
- `workflow_state`: compatibility facade for workflow state helpers
- `state_checks`: ready checks and structural review
- `state_transitions`: transitions and dependent staleness propagation
- `state_packets`: semantic packet building
- `workflow_io`: compatibility facade for workflow IO helpers
- `io_archive`: audit file archiving
- `io_export`: manifests, relations, and JSON export helpers
- `io_import`: Markdown and manifest import helpers
- `storage` and `migrations`: SQLite engine/session helpers plus Alembic lifecycle
- `llm`: provider routing facade
- `llm_types`: shared response dataclass and schema constants
- `llm_payloads`: request builders, call-id resolution, and mock provider behavior
- `llm_transport`: HTTP transport, retry, backoff, and provider error mapping
- `llm_validation`: provider payload parsing and response text extraction
- `llm_common` and `llm_*`: compatibility facades and provider-specific entrypoints
- `service`: compatibility facade for older imports
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
```

- `state.db`: SQLite source of truth
- `backups/`: timestamped database backups
- `exports/`: JSON manifests and SQL dumps
- `logs/`: reserved for future automation logs

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
- `provider_call_audits`
- `provider_call_audits.events_json`

## Review Split

### Structural review

Structural review is code-driven and must be deterministic.

It checks:

- artifact type, slug, round, and project alignment
- source file existence
- required frontmatter presence
- dependency approval rules
- dependency graph cycles

### Semantic review

Semantic review is LLM-assisted.

The backend prepares a structured review packet containing:

- artifact identity
- upstream and downstream references
- current metadata and body snapshot
- a rubric tailored to the artifact type

The LLM should return structured JSON so the result can be recorded without weakening consistency controls.

## Lifecycle

Recommended artifact states:

- `draft`
- `structurally_valid`
- `semantic_review`
- `approved`
- `rejected`
- `stale`
- `superseded`
- `archived`

## Database Maintenance

Supported workflows:

- `uv run fpa db init`
- `uv run fpa db migrate`
- `uv run fpa db check`
- `uv run fpa db backup`
- `uv run fpa db restore --from ...`
- `uv run fpa db wipe --yes`

## Import And Export

- `uv run fpa import markdown-scan --project <key>`
- `uv run fpa import markdown-scan --project <key> --apply`
- `uv run fpa export manifest --project <key>`
- `uv run fpa export relations --project <key>`
- `uv run fpa export sql`

## Skill Integration Rule

When the skill needs workflow state, it should call CLI commands instead of inferring graph consistency from Markdown alone.

## Environment Configuration

Use `.env` for runtime configuration so the same skill can target different providers and project layouts without code edits.

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
