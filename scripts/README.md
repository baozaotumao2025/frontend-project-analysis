# Development Commands

This directory contains short wrappers around the project maintenance commands.
The E2E entries below are maintainer-only regression checks and are not part of the
normal end-user workflow.

## Test

- `./scripts/test-smoke.sh`: fast CLI and compatibility regression checks
- `./scripts/test-check.sh`: compile check plus smoke tests
- `./scripts/test-e2e.sh`: default E2E regression suite
- `./scripts/test-e2e-install.sh`: install and init E2E coverage
- `./scripts/test-e2e-flow.sh`: multi-round workflow recovery E2E coverage
- `./scripts/test-e2e-reset.sh`: force reset E2E coverage
- `./scripts/test-full.sh`: full test suite
- `./scripts/test-all.sh`: compile, smoke, and full tests

## Lint

- `./scripts/lint.sh`: Ruff lint over `src/frontend_project_analysis` and `tests`

## Make Targets

- `make smoke`
- `make e2e`
- `make e2e-install`
- `make e2e-flow`
- `make e2e-reset`
- `make full`
- `make check`
- `make lint`
- `make all`

## Updating The Skill

When this skill changes, reinstall or refresh the installed copy in the target
environment, then start a new Codex thread so the updated skill content is
picked up reliably.
