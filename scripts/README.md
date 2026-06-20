# Development Commands

This directory contains short wrappers around the project maintenance commands.
The E2E entries below are maintainer-only regression checks and are not part of the
normal end-user workflow.

For automation and maintenance logic, treat the shell scripts as the canonical
entrypoints. Use `make` for grouped, human-friendly aliases.
See [`references/command-layer.md`](../references/command-layer.md) for the
full command hierarchy policy.

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

## Release

- `./scripts/release-preflight.sh`: release-time test, lint, path-leak, version, and parity-audit launcher
- `./scripts/release-llm-review.sh`: release packet generator for a fresh-session LLM review
- `./scripts/release-card.sh`: minimal fresh-session reviewer card generator after preflight
- `./scripts/release.sh`: release preflight followed by fresh-session LLM review packet generation
- `./scripts/release-publish.sh`: maintainer publish flow that runs preflight, regression, review, version checks, commit, tag, and push

## Make Targets

Prefer the grouped targets first: `make test`, `make quality`, and `make release`.
Primary grouped targets use dotted names; hyphenated names remain compatibility aliases.

Quick selection:

| Scenario | Recommended entry |
| --- | --- |
| Human-friendly grouped entrypoint | `make test`, `make quality`, or `make release` |
| Canonical automation layer | `scripts/*.sh` |
| Skill-side repository maintenance | Call the script directly, then add a `make` alias only if humans need a grouped shortcut |

Primary targets:

- `make help`
- `make test`
- `make quality`
- `make e2e`
- `make release`
- `make test.smoke`
- `make test.full`
- `make test.check`
- `make test.e2e`
- `make test.e2e-install`
- `make test.e2e-flow`
- `make test.e2e-reset`
- `make quality.compile`
- `make quality.lint`
- `make release.preflight`
- `make release.packet`
- `make release.card`

Compatibility aliases:

- `make release-card`

## Updating The Skill

When this skill changes, reinstall or refresh the installed copy in the target
environment, then start a new Codex thread so the updated skill content is
picked up reliably.
