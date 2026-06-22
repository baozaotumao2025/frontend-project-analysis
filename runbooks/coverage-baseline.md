# Coverage Baseline

## Purpose

This runbook records the repository's quantitative test coverage baseline and
the supported command for reproducing it.

## Scope

- Measured source scope: `src/frontend_project_analysis`
- Measurement command: `make test.coverage`
- Underlying runner: `./scripts/test-coverage.sh`

## Baseline

| Date | Exact coverage | Covered lines | Total statements |
| --- | --- | --- | --- |
| 2026-06-22 | `80.66842991103631%` | `2867` | `3407` |

## How To Reproduce

1. Run `make test.coverage`.
2. Review the `coverage report --show-missing` output.
3. Compare the current number against the baseline above.

## Guardrail

The coverage report is configured with `fail_under = 80.66` in
[`pyproject.toml`](../pyproject.toml). That keeps the current baseline enforced
while leaving a small rounding buffer above the exact measured value.

If the guardrail fails, do not relax it silently. Re-run the suite, confirm the
scope has not changed, and then decide whether the baseline should be updated
deliberately.
