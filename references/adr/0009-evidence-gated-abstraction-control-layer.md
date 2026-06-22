# ADR 0009: Evidence-Gated Abstraction Control Layer

## Status

Accepted

## Context

The workflow already has revision-aware lifecycle gates, derived index/matrix projections, and fresh-context host review isolation.

That is enough to keep the canonical round chain consistent, but large later-round batches still create a practical risk:

- the reviewer may assume it has covered every related file when it has not
- relation-heavy rounds may drift between generation and review
- a packet can become a moving target if new evidence appears while the review is in progress
- users need an explicit way to know whether a file is mapped, excluded, or still needs review

We want to keep the existing Persona -> Story Map -> Page -> Feature -> GWT -> Feature Spec chain, but add a stricter control surface in front of each semantic step.

## Decision

We add an evidence-gated abstraction layer above the existing round workflow.

Specifically:

- each round first enumerates its `analysis_inventory`
- every in-scope item must be reconciled into a `coverage ledger` disposition
- the review input is a `frozen packet` built from the inventory, coverage, upstream fresh revisions, and prompt bundle
- generation and verification remain separate concerns
- review must happen in an `independent worker` context when host mode is used
- code continues to own file presence, freshness, dependency validity, and gate enforcement

This layer is documented in `references/evidence-gated-abstraction.md` and reflected in `references/workflow.md`, `references/validation-matrix.md`, and `references/schema-sketch.md`.

## Alternatives Considered

### Rely on the existing revision-aware gates only

Rejected because lifecycle freshness alone does not prove that all relevant evidence was enumerated and reconciled.

### Add a separate review workflow instead of a control layer

Rejected because that would duplicate the round chain and make the system harder to understand.

### Encode coverage state only in Markdown files

Rejected because coverage needs to stay reconciled with the workflow database and the review packet.

## Consequences

- Later rounds gain an explicit inventory and coverage checkpoint.
- Review packets become more stable and easier to reason about.
- Humans can distinguish `mapped`, `excluded`, and `needs_review` outcomes instead of inferring them.
- The repository keeps a stronger separation between artifact lifecycle and evidence control.
- README and skill entrypoints can stay concise by pointing to the canonical references instead of restating the control layer.

## Notes

- `references/evidence-gated-abstraction.md` defines the control loop and terminology.
- `references/schema-sketch.md` defines where coverage-related state belongs.
- `references/workflow.md` defines how the control layer wraps each round.
- `references/validation-matrix.md` defines what code checks versus what semantic review checks.
- `references/adr/0004-host-review-fresh-context-isolation.md` remains the source for host review isolation.
