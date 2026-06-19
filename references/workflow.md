# Workflow

This page defines the analysis workflow round contract.

For a fresh target repository, bootstrap the project first with `uv run fpa install`, then `uv run fpa init --project <key> --name <name>`. After that, use the round gates and artifact commands below to move through the workflow.

## Gate Contract

- Each round MUST consume only approved and fresh upstream revisions.
- If a required upstream revision is stale, the round MUST NOT advance.
- A failed gate MUST NOT mutate the current revision state.
- Before starting a downstream round, run `uv run fpa workflow start --project <key> --round <n>`; this command hard-checks that the upstream round revisions are approved and fresh before the round can continue.

## Recovery Contract

- Recovery MUST be performed by creating a new revision for the earliest affected round.
- Approved revisions MUST NOT be edited in place.
- Downstream stale revisions MUST be revalidated before they can progress again.

### Recovery Matrix

Use this matrix as the operator-facing lookup when a later round reveals that an earlier round changed:

| Round | Stale source | Wrong recovery layer | Correct recovery layer | Blocked ref |
| --- | --- | --- | --- | --- |
| 4 | `page:customer-profile` | `feature:customer-assignment` | `page:customer-profile` | `page:customer-profile` |
| 5 | `page:customer-profile` | `gwt:customer-assignment` | `feature:customer-assignment` | `feature:customer-assignment` |
| 6 | `page:customer-profile` | `feature_spec:customer-assignment` | `gwt:customer-assignment` | `gwt:customer-assignment` |

The table mirrors the regression matrix in `tests/test_cli_workflow_gate.py`: a lower downstream layer may be revalidated, but the gate remains blocked until the exact round input has been revalidated and approved.

## Round 1: Persona Definition

- Input: project description
- Output: `docs/personas/index.md` and `docs/personas/[persona-name].md`
- Each Persona should include name, core goal, key differences, permission boundary, and invisible pages or capabilities
- Before approval, register or import the resulting artifacts into the SQLite workflow state
- Round 1 may start from raw project description; no upstream artifact gate applies
- A Persona revision MUST reach `approved` before Round 2 can consume it

Persona split rules:

- Split into separate Persona only when goals, decisions, or core paths truly differ
- If the path is the same and only permissions differ, keep one Persona and explain the permission boundary

## Round 2: Story Map

- Input: approved `docs/personas/*.md`
- Output: `docs/story-maps/index.md` and `docs/story-maps/[persona-name].md`
- One Story Map per Persona
- Format: `Activity -> Step -> Story`
- Do not mention pages or Features
- Semantic review should judge business coherence; structural review still runs via CLI
- If no external LLM is configured, use `FPA_LLM_PROVIDER=host` and let the current Codex or Claude Code session automatically judge the semantic packet
- Round 2 MUST consume only `approved` Persona revisions that are not `stale`
- If a Persona revision changes later, any Story Map revision that depends on it becomes stale and MUST be revalidated and approved before it can feed Round 3

## Round 3: Page Map

- Input: approved `docs/story-maps/*.md`
- Output: `docs/pages/index.md`, `docs/pages/[page-slug].md`, and `docs/relations/persona-story-page-matrix.md`
- Map Story Steps into page, modal, drawer, or tab surfaces
- Round 3 MUST consume only `approved` Story Map revisions that are not `stale`
- If an upstream Story Map changes, all derived page revisions become stale instead of being rewritten in place

## Round 4: Feature Slicing

- Input: approved `docs/pages/*.md`
- Output: `docs/features/index.md`, `docs/features/[feature-name].md`, and `docs/relations/feature-coverage-matrix.md`
- Process 1-3 pages at a time, then pause
- Each Feature should record name, page, responsibility, state type, cross-page reuse, and source story
- Round 4 MUST consume only `approved` Page revisions that are not `stale`
- If a Page revision changes later, derived Feature revisions become stale and MUST be revalidated

## Round 5: Given-When-Then

- Input: approved `docs/features/*.md`
- Output: `docs/gwt/[feature-name].feature`
- Process one Feature at a time, then pause
- Round 5 MUST consume only `approved` Feature revisions that are not `stale`
- If a Feature revision changes later, its GWT revision becomes stale

## Round 6: Feature Spec And Delivery Planning

- Input: all approved artifacts
- Output: `specs/features/[feature-name]-spec.md`
- Generate one Feature Spec per Feature
- Final release planning should rely on recorded dependency edges and approval state, not on manual matrix edits alone
- Round 6 MUST consume only approved and fresh upstream revisions across the full chain
- If any upstream revision changes after a spec is approved, the spec becomes stale and MUST be regenerated

## Cross-Round Recovery

If Round 3 or later reveals that a Round 1 artifact needs to change:

- create a new revision for the earlier-round artifact
- do not mutate the already approved revision in place
- mark every downstream artifact revision that depended on the older revision as `stale`
- re-run the earliest affected round gate and then continue forward again

This keeps the workflow auditable and preserves the approved history that downstream work was originally based on.
