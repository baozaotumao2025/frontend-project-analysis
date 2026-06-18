# ADR 0001: Revision-Aware State Gates And Recovery

## Status

Accepted

## Context

The workflow produces a chain of analysis artifacts: `Persona` -> `Story Map` -> `Page` -> `Feature` -> `GWT` -> `Feature Spec`.

We need three properties at the same time:

- Each stage must only consume approved upstream inputs.
- If an earlier stage changes after later stages already exist, downstream work must be invalidated deterministically.
- The approved history must remain auditable and never be rewritten in place.

The repository already stores artifact versions and transition history, so the lifecycle can be modeled as revision-aware rather than as a single mutable blob.

## Decision

We model the workflow as a revision-aware lifecycle with explicit gates:

- A stage may start only when its upstream revision is `approved` and not `stale`.
- A later-stage artifact that depends on a changed upstream revision becomes `stale`.
- Recovery is performed by creating a new revision for the earlier-stage artifact, not by editing the already approved revision in place.
- When a new revision is approved, the old revision may be marked `superseded`, and downstream artifacts that depended on it remain stale until revalidated.

We keep these rules in `references/state-machine.md`, `references/workflow.md`, and `references/quality-gates.md`, not in `README.md`.

## Alternatives Considered

### Mutate approved artifacts in place

Rejected because it destroys auditability and makes downstream history ambiguous.

### Allow later stages to continue with stale upstream inputs

Rejected because it creates hidden coupling and allows invalid outputs to look current.

### Store only a flat status without revision lineage

Rejected because rollback and recovery would be under-specified and hard to enforce.

## Consequences

- The workflow becomes stricter, but also easier to reason about.
- Gate failures are deterministic and local to a revision.
- Historical approvals remain available for audits and reviews.
- Recovery requires revalidating and approving the earliest affected stage, then replaying the downstream path.

## Notes

- `README.md` should stay high-level and point readers to the canonical references.
- `references/state-machine.md` defines lifecycle semantics.
- `references/workflow.md` defines round-by-round gates and recovery.
- `references/quality-gates.md` defines the validation checklist.
