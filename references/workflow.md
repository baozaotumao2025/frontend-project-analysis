# Workflow

This page defines the analysis workflow round contract.

For a fresh target repository, prepare a user-owned brief first, then confirm it, then run `uv run fpa init --project <key> --name <name> --brief-file <path>` or `uv run fpa init --project <key> --name <name> --brief <text>` with confirmed brief metadata. If the brief is not ready yet, use `uv run fpa brief interview --output <path>` to collect one in a bounded Q&A flow, optionally add `--transcript <path>` to keep the conversation log, then run `uv run fpa brief confirm --input <path> --output <confirmed-path>` before `init`. If you want LLM-assisted follow-up and synthesis, use `uv run fpa brief assistant --output <path>` instead; it also produces a draft brief that must be confirmed before `init`. After that, use the round gates and artifact commands below to move through the workflow.

## Gate Contract

- Each round MUST consume only approved and fresh upstream revisions.
- If a required upstream revision is stale, the round MUST NOT advance.
- A failed gate MUST NOT mutate the current revision state.
- Before starting a downstream round, run `uv run fpa workflow start --project <key> --round <n>`; this command hard-checks that the upstream round revisions are approved and fresh before the round can continue.

## Explore Contract

- `Explore mode` is a non-canonical analysis path for discovery and iterative refinement.
- It may read draft or otherwise unapproved upstream material so users can inspect later-round structure while still revising earlier-round intent.
- `Explore mode` must not advance canonical lifecycle state or overwrite approved history.
- Use `uv run fpa workflow explore start --project <key> --round <n>` when you want the discoverable exploratory entrypoint.

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
The same repository keeps `Explore mode` separate from this canonical path so exploratory analysis can continue without claiming approval.

## Round 1: Persona Definition

- Input: `analysis/brief.md`
- Output: `analysis/personas/index.md` and `analysis/personas/[persona-name].md`
- Each Persona should include name, core goal, key differences, permission boundary, and invisible pages or capabilities
- Before approval, register or import the resulting artifacts into the SQLite workflow state
- Round 1 starts from `analysis/brief.md` and no upstream artifact gate applies
- A Persona revision MUST reach `approved` before Round 2 can consume it
- If the repository has no brief yet, collect one first with `uv run fpa brief interview --output <path>` or `uv run fpa brief assistant --output <path>`, confirm it with `uv run fpa brief confirm --input <path> --output <confirmed-path>`, and save the confirmed result into `analysis/brief.md` before generating Round 1 artifacts

Persona split rules:

- Split into separate Persona only when goals, decisions, or core paths truly differ
- If the path is the same and only permissions differ, keep one Persona and explain the permission boundary

## Round 2: Story Map

- Input: approved `analysis/personas/*.md`
- Output: `analysis/story-maps/index.md` and `analysis/story-maps/[persona-name].md`
- One Story Map per Persona
- Format: `Activity -> Step -> Story`
- Do not mention pages or Features
- Semantic review should judge business coherence; structural review still runs via CLI
- If no external LLM is configured, use `FPA_LLM_PROVIDER=host` and let a fresh Codex or Claude Code reviewer context judge the frozen semantic packet; when Codex can spawn a sub-agent, that is the required execution path
- Round 2 MUST consume only `approved` Persona revisions that are not `stale`
- If a Persona revision changes later, any Story Map revision that depends on it becomes stale and MUST be revalidated and approved before it can feed Round 3

## Round 3: Page Map

- Input: approved `analysis/story-maps/*.md`
- Output: `analysis/pages/index.md`, `analysis/pages/[page-slug].md`, and `analysis/relations/persona-story-page-matrix.md`
- Map Story Steps into page, modal, drawer, or tab surfaces
- Round 3 MUST consume only `approved` Story Map revisions that are not `stale`
- If an upstream Story Map changes, all derived page revisions become stale instead of being rewritten in place

## Round 4: Feature Slicing

- Input: approved `analysis/pages/*.md`
- Output: `analysis/features/index.md`, `analysis/features/[feature-name].md`, and `analysis/relations/feature-coverage-matrix.md`
- Process 1-3 pages at a time, then pause
- Each Feature should record name, page, responsibility, state type, cross-page reuse, and source story
- Round 4 MUST consume only `approved` Page revisions that are not `stale`
- If a Page revision changes later, derived Feature revisions become stale and MUST be revalidated

## Round 5: Given-When-Then

- Input: approved `analysis/features/*.md`
- Output: `analysis/gwt/[feature-name].feature`
- Process one Feature at a time, then pause
- Round 5 MUST consume only `approved` Feature revisions that are not `stale`
- If a Feature revision changes later, its GWT revision becomes stale

## Round 6: Feature Spec And Delivery Planning

- Input: all approved artifacts
- Output: `analysis/specs/features/[feature-name]-spec.md`
- Generate one Feature Spec per Feature
- Final release planning should rely on recorded dependency edges and approval state, not on manual matrix edits alone
- Round 6 MUST consume only approved and fresh upstream revisions across the full chain
- If any upstream revision changes after a spec is approved, the spec becomes stale and MUST be regenerated
- Feature Spec should make discovery evidence, risks, assumptions, accessibility, observability, release, and compliance constraints explicit when they affect delivery

## Cross-Round Recovery

If Round 3 or later reveals that a Round 1 artifact needs to change:

- create a new revision for the earlier-round artifact
- do not mutate the already approved revision in place
- mark every downstream artifact revision that depended on the older revision as `stale`
- re-run the earliest affected round gate and then continue forward again

This keeps the workflow auditable and preserves the approved history that downstream work was originally based on.
