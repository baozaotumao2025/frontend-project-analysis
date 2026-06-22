# Evidence-Gated Abstraction

## Purpose

This document defines the control layer that keeps analysis work inside an explicit evidence boundary.

The workflow still produces Persona, Story Map, Page, Feature, GWT, and Feature Spec artifacts. This layer adds a stricter rule around how each round sees files:

- enumerate the available evidence first
- reconcile every file into a known disposition
- freeze the packet before review
- separate generation from verification
- let code enforce the gate

## Core Terms

| Term | Meaning |
| --- | --- |
| `analysis_inventory` | The explicit file and relation set that a round is allowed to inspect |
| `coverage ledger` | The per-file disposition table for the current round |
| `mapped` | The file or relation is included in the current round's evidence set |
| `excluded` | The file is intentionally not used in the current round, with a stated reason |
| `needs_review` | The file or relation cannot yet be classified safely and must be revisited |
| `frozen packet` | A snapshot of inventory, coverage, upstream revisions, and prompt bundle for review |
| `independent worker` | A reviewer context that does not reuse the drafting context |

## Control Loop

Each round SHOULD follow this order:

1. Enumerate the current round inventory.
2. Reconcile every item into `mapped`, `excluded`, or `needs_review`.
3. Freeze the packet once the evidence set is stable.
4. Run generation or review only against the frozen packet.
5. Use code to block downstream progress if coverage or freshness is incomplete.

## Round Inputs And Outputs

| Round | Evidence input | Primary output | Coverage output |
| --- | --- | --- | --- |
| Brief | project brief sources | `analysis/brief.md` | brief provenance and open assumptions |
| Round 1 | `analysis/brief.md` + inventory | Persona files | Persona coverage ledger |
| Round 2 | approved Persona + inventory | Story Map files | Persona-to-story coverage ledger |
| Round 3 | approved Story Map + inventory | Page files + page matrix | story-to-page coverage ledger |
| Round 4 | approved Page set + batch inventory | Feature files + feature matrix | page-to-feature coverage ledger |
| Round 5 | approved Feature + packet | GWT file | scenario coverage ledger |
| Round 6 | all approved upstream artifacts + packet | Feature Spec | delivery-risk coverage ledger |

## What The Layer Guarantees

- No round depends on an implicit "I probably saw everything" judgment.
- Every file in scope must have a recorded disposition.
- A review packet is always a frozen snapshot, not an evolving conversation.
- Semantic review can judge meaning, but code still owns presence, freshness, and dependency checks.
- If coverage is incomplete, the next round gate does not open.

## What It Does Not Replace

- It does not replace `approved`, `fresh`, or `stale`.
- It does not replace the Persona / Story Map / Page / Feature / GWT / Feature Spec chain.
- It does not replace the index or relation matrices.
- It does not let semantic review decide whether a required file exists.

## Integration Rule

Treat this layer as a per-round control surface:

- `analysis/*/index.md` remains the browsing projection
- `analysis/relations/*.md` remains the lineage projection
- `analysis_inventory` and the `coverage ledger` remain the round's checking surface
- the `frozen packet` remains the review input
- `workflow start` and the state machine remain the final gate

If a new artifact is discovered after freezing, the packet is invalidated and the round must reconcile again before review continues.
