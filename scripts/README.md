# Development Commands

This directory contains short wrappers around the project maintenance commands.

## Test

- `./scripts/test-smoke.sh`: fast CLI and compatibility regression checks
- `./scripts/test-check.sh`: compile check plus smoke tests
- `./scripts/test-full.sh`: full test suite
- `./scripts/test-all.sh`: compile, smoke, and full tests

## Lint

- `./scripts/lint.sh`: Ruff lint over `src/frontend_project_analysis` and `tests`

## Make Targets

- `make smoke`
- `make full`
- `make check`
- `make lint`
- `make all`

