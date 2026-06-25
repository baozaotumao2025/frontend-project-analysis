# Release Docs And Terminology Audit

## Purpose

Use this runbook to verify that implementation files and description files still agree before a public release.

For a quick deterministic launcher, run `./scripts/release-preflight.sh` first.

## When To Run

- After the normal test and lint preflight passes
- Before creating the release commit or tag
- Every time a change touches public commands, workflow behavior, file layout, or vocabulary

## Audit Steps

1. Collect the changed surface.
   - Review the current diff and split files into implementation files such as `src/`, `tests/`, `migrations/`, and `scripts/`, and description files such as `README.md`, `SKILL.md`, `references/`, `runbooks/`, and `AGENTS.md`.
2. Check logic alignment.
   - For every changed command, file path, or public behavior in code, confirm the matching description file was updated.
   - For every changed claim in a description file, confirm the corresponding code path, test, or workflow rule exists.
   - If a description mentions a command or file that no longer exists, fix the description or the code before release.
3. Check terminology alignment.
   - Treat `references/glossary.md` as the authoritative vocabulary.
   - Keep English-only terms exactly as written.
   - Add any new domain term to the glossary before using it elsewhere.
   - Look for translated substitutes, alternate spellings, or mixed casing in the changed files.
4. Check the canonical references that define repository behavior.
   - `README.md`, `SKILL.md`, and `references/document-map.md` should still agree on authority and reading order.
   - `references/cli-contract.md`, `references/state-entrypoints.md`, `references/quality-gates.md`, and the relevant `runbooks/*` files should reflect any changed command or workflow behavior.
   - Re-check ADR scope before release.
   - Changes that only refine projection files, export surfaces, or reference-layer presentation normally stay in `references/*` and do not need a new ADR.
   - Add or revise an ADR only when the release introduces a new durable architectural boundary, lifecycle rule, authority split, or governance decision.
5. Record the result.
   - `OK`: no mismatch remains.
   - `WARN`: the mismatch is intentional and documented as future work.
   - `FAIL`: any untracked mismatch remains; do not tag.

## Practical Checks

- Search for public surface references:
  - `rg -n "fpa |make |./scripts/|src/frontend_project_analysis/|release.publish|release-publish" README.md SKILL.md references runbooks`
- Search for terminology drift:
  - `rg -n "Persona|Story Map|Page Map|Feature Slicing|Feature Spec|Happy Path|Edge Case|Permission Case|Error Case|server state|client state|Shared Component" README.md SKILL.md references runbooks src tests`
- Search for stale absolute paths:
  - `rg -n "/Users/cherubines/Documents/MaxCPA" README.md SKILL.md references frontend-decomposition-methodology.md AGENTS.md --glob '!references/release-checklist.md'`
