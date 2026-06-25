# ADR Relationship Map

This page records the stable relationship between the repository ADRs so that
new decisions can be checked against existing boundaries.

## Core Dependencies

| ADR | Depends on | Boundary |
| --- | --- | --- |
| `0001-revision-aware-state-gates` | `references/state-machine.md`, `references/workflow.md`, `references/quality-gates.md` | Defines canonical lifecycle and stale propagation |
| `0002-document-layering-and-rule-placement` | Repository documentation structure | Defines where stable rules and rationale belong |
| `0003-cross-cutting-analysis-and-brief-convergence` | `0001`, `references/methodology.md`, `references/templates.md` | Extends the workflow with cross-cutting concerns without changing the six-round model |
| `0004-host-review-fresh-context-isolation` | `references/infrastructure.md`, `references/validation-matrix.md`, `references/cli-contract.md` | Defines host review isolation only |
| `0005-review-resubmit-and-import-first-reconciliation` | `0001`, `0004`, `references/state-entrypoints.md` | Defines the recovery path for manual Markdown edits and stale revisions |
| `0006-formal-and-explore-workflow-modes` | `0001`, `references/state-machine.md`, `references/workflow.md` | Splits exploratory analysis from canonical delivery |
| `0007-locale-tolerant-cross-reference-resolution` | `references/templates.md`, `tests/test_workflow_state_integrity.py` | Defines allowed cross-reference forms without changing identity semantics |
| `0008-llm-managed-submission-intent-routing` | `references/downstream-commit-policy.md`, `src/frontend_project_analysis/core/prompts.py`, `src/frontend_project_analysis/core/config.py` settings, `brief assistant` prompt architecture | Defines natural-language routing only; does not define submission policy |
| `0009-evidence-gated-abstraction-control-layer` | `0001`, `0004`, `references/evidence-gated-abstraction.md`, `references/validation-matrix.md` | Defines the inventory, coverage, frozen packet, and independent worker control layer without changing canonical artifact identity |

## Relationship Notes

- `0001` is the lifecycle base layer. `0005` and `0006` extend its consequences, but neither changes the lifecycle rules themselves.
- `0004` and `0005` overlap on host review context, but `0004` defines the isolation rule and `0005` defines the recovery flow that uses it.
- `0008` must stay separate from `references/downstream-commit-policy.md`.
  - `0008` answers: "which path should the request follow?"
  - `references/downstream-commit-policy.md` answers: "what is a valid downstream submission bundle and how is it released?"
- `0008` also must stay separate from `0004` and `0005`.
  - those ADRs control review isolation and recovery
  - `0008` only routes intent before a workflow begins

## Conflict Watch

When adding or changing an ADR, check for the following accidental overlaps:

- lifecycle semantics changing inside an ADR that is supposed to be only about documentation placement or routing
- review isolation requirements being restated in a submission policy
- downstream submission policy being used as a synonym for natural-language routing
- prompt-template override behavior being hard-coded in command handlers instead of shared prompt builders
- projection or export-surface refinements being promoted to a new ADR even though they only restate current reference-layer behavior and do not change lifecycle, authority, or governance boundaries

## Reading Order

Recommended order for related decisions:

1. `0001` for lifecycle semantics
2. `0002` for document placement
3. `0004` and `0005` for host review and recovery
4. `0006` for explore-mode behavior
5. `0007` for reference resolution
6. `0008` for submission routing
7. `0009` for evidence-gated control-layer boundaries
