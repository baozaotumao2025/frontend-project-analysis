# ADR 0006: Formal And Explore Workflow Modes

## Status

Accepted

## Context

The current workflow is intentionally revision-aware and gate-driven.
That makes formal delivery auditable, but it also means exploratory front-end analysis can feel brittle when the user wants to revise earlier-round thinking while already looking at later-round output.

In practice, the workflow serves two different jobs:

- formal delivery, where every downstream artifact must only consume `approved` and `fresh` upstream revisions
- exploratory analysis, where users want to inspect later-round structure while still revising earlier-round intent

Using one strict gate model for both jobs increases friction and turns normal discovery work into repeated revalidation.

## Decision

We introduce two explicit user-facing workflow modes:

- `Formal mode`
- `Explore mode`

### Formal mode

Formal mode preserves the current canonical behavior:

- downstream rounds consume only `approved` and `fresh` upstream revisions
- `stale` revisions block progression
- recovery happens by creating a new revision for the earliest affected round
- approved history remains append-only and auditable

### Explore mode

Explore mode is a non-canonical analysis path for discovery and iterative refinement:

- later-round analysis may read upstream draft material or otherwise unapproved intermediate output
- the user can revise earlier-round content without stopping to complete a full approval loop first
- the output of Explore mode is not treated as canonical workflow state until it is explicitly committed through Formal mode
- Explore mode must never overwrite or silently upgrade canonical revisions

### Mode boundary

Switching from Explore mode to Formal mode requires an explicit commit or freeze step.
That step re-imports or revalidates the chosen inputs, then re-enters the canonical gate path.

## Why This Decision

- It preserves the strong consistency model where it matters: the canonical chain.
- It gives front-end analysts a low-friction place to think, compare, and revise.
- It separates discovery from delivery instead of forcing one workflow to do both jobs at the same time.
- It keeps auditability intact because only Formal mode can advance canonical lifecycle state.

## Alternatives Considered

### Relax the gates globally

Rejected because it weakens auditability and blurs the distinction between exploratory and approved work.

### Keep one strict mode and improve recovery only

Rejected because it still forces exploratory users to pay full approval cost while they are still learning the problem.

### Allow Explore mode to mutate canonical state directly

Rejected because it would reintroduce hidden coupling and make approved history ambiguous.

## Consequences

- The user chooses between certainty and flexibility up front.
- Formal delivery stays conservative and predictable.
- Exploratory work becomes easier to iterate on, but must be explicitly promoted before it can be treated as official.
- The implementation must keep the two modes clearly separated in CLI behavior, state handling, and documentation.

## Notes

- `references/state-machine.md` continues to define canonical lifecycle semantics.
- `references/workflow.md` continues to define the formal round contract.
- `references/state-entrypoints.md` already lists the mode-specific entrypoints for both formal and explore paths.
- `references/cli-contract.md` should describe the user-visible difference between the two modes after implementation.
