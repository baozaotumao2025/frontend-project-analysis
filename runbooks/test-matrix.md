# Test Matrix

## Purpose

This document describes the preferred test strategy for proving that the skill is
working end-to-end and is safe to release.

The goal is not just to see green checks. The goal is to prove that every user-
visible command, state transition, and derived projection still behaves as the
workflow contract expects.

## Test Principles

- Test the contract, not the implementation detail.
- Prefer a layered strategy: smoke, integration, state/domain, E2E, and release gate.
- Every critical command should have at least one positive path and one negative path.
- Every important state transition should be covered by a direct assertion.
- Every recovery flow should prove that the system can continue after failure.
- If a test proves a projection or matrix, also verify the source graph or database.

## Test Layers

| Layer | Purpose | Typical scope | Example evidence |
| --- | --- | --- | --- |
| Smoke | Confirm CLI wiring and import compatibility | help text, command registration, basic entrypoints | `tests/test_cli_smoke.py` |
| Integration | Confirm one command or one small flow | import, review, db, project helpers | `tests/test_cli_import_flows.py`, `tests/test_cli_review_flows.py`, `tests/test_cli_project_db.py` |
| State / Domain | Confirm lifecycle rules and dependency logic | state transitions, freshness, approval, structural checks | `tests/test_workflow_state_transitions.py`, `tests/test_workflow_state_integrity.py`, `tests/test_cli_workflow_gate.py` |
| E2E | Confirm a full release-relevant workflow | init, brief, recovery, restore, stale propagation | `tests/test_cli_e2e.py` |
| Release Gate | Confirm the repository is ready to publish | lint, full test run, version consistency, docs contract | `../references/release-checklist.md`, `README.md` |

## Coverage Matrix

| Capability | Must prove | Recommended evidence |
| --- | --- | --- |
| `brief interview` | Collects a user-owned brief and can write transcript output | interactive CLI test plus output file assertion |
| `init` / `project init` | Creates local state, analysis workspace, and `.gitignore` entry | filesystem assertions and idempotency check |
| `artifact add` | Creates `draft` only | state assertion after add |
| `artifact link` | Writes dependency edges and can stale approved downstream work | dependency graph assertion plus stale propagation assertion |
| `artifact ready` | Reports ready artifacts without mutating state | read-only assertion before and after call |
| `review structural` | Enforces structural checks and advances to `structurally_valid` | successful path and a missing-section failure path |
| `review semantic-run` | Emits packet, records semantic result, and respects auto-approve | host mode, mock mode, and auto-approve on/off |
| `review semantic-record` | Records externally produced review results correctly | payload ingestion and resulting status assertion |
| `review approve` | Only approves eligible revisions and respects hard dependencies | success path and blocked approval path |
| `review reject` | Can reject draft, structurally_valid, semantic_review, approved, and stale revisions | state assertions plus gate failure assertion |
| `workflow start` | Hard-blocks when upstream rounds are not approved and fresh | blocked round scenarios and exact blocking ref |
| `workflow gate` | Mirrors the diagnostic state of the round gate | pass/fail parity with `workflow start` |
| `import manifest` | Ignores inbound status as a lifecycle override | apply and preview checks |
| `import markdown-scan` | Ignores frontmatter status override and refreshes projections | body scan, index refresh, matrix refresh |
| `export manifest` / `export relations` | Produces consistent projections from current state | exported files plus graph consistency |
| `db backup` / `db restore` | Can recover state from a snapshot | backup path existence, restore payload, post-restore assertions |
| `db wipe` | Deletes workflow state when explicitly requested | database file absence plus clean re-init |

## Minimum Release Suite

Before any public release, run at least:

1. `uv run pytest -q`
2. `uv run ruff check src/frontend_project_analysis tests`
3. A focused E2E pass for the release-relevant paths:
   - `brief interview`
   - `init`
   - `review structural`
   - `review semantic-run`
   - `review semantic-record`
   - `review approve`
   - `review reject`
   - `artifact link`
   - `workflow start`
   - `db backup`
   - `db restore`
4. A docs-contract pass:
   - `README.md`
   - `SKILL.md`
   - `references/document-map.md`
   - `references/release-checklist.md`

## Recommended Order

1. Smoke tests first
2. State/domain tests next
3. Integration tests after that
4. E2E last
5. Release gate checks at the very end

This order fails fast on wiring and lifecycle regressions before spending time on
longer full-flow validation.

## Existing Test Coverage

| Area | Existing focus | Notes |
| --- | --- | --- |
| CLI wiring | smoke | good for top-level entrypoint regressions |
| Import/export | integration | good for projection and status override rules |
| Review flows | integration | good for semantic and structural review behavior |
| Workflow gates | state/domain | good for freshness, stale propagation, and approval gating |
| E2E recovery | end-to-end | good for publishable workflow confidence |

## Practical Rule

If a feature can fail in production because of state, dependency freshness, or
projection drift, it needs a direct test.

If a feature is only about narrative quality or semantic fit, it still needs at
least one state-safe path around the review flow so the workflow can continue.
