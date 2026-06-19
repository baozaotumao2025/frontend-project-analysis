# ADR 0005: Review Resubmit And Import-First Reconciliation

## Status

Accepted

## Context

Workflow-managed Markdown is an editable projection layer, while SQLite remains the authoritative state store.

That split creates two operational requirements:

- users need a fast recovery path after they edit Markdown by hand
- the system must not silently treat edited Markdown as canonical before re-import

We also want host semantic review to remain isolated from the drafting context without requiring a different model.

In Codex environments, the practical way to achieve that isolation is a fresh sub-agent context.

## Decision

We make `fpa review resubmit` the canonical operator recovery command for Markdown edits and stale revisions.

The command MUST:

- re-import the target workspace before any review decision is made
- rerun structural review against the current files
- continue semantic review in one of two ways:
  - non-host provider: complete the semantic review immediately
  - `host` provider: export a frozen semantic packet for a fresh reviewer context

We allow a brief temporary mismatch between the Markdown tree and SQLite after manual edits, but only as a bounded input window.
That mismatch is not canonical state and MUST be resolved by `import markdown-scan --apply` or `review resubmit` before downstream review or gate decisions continue.

When host review is available in a Codex environment, the reviewer context MUST be a fresh sub-agent with `fork_context: false`.
The reviewer output MUST include counterexamples and evidence-backed findings, otherwise the result is downgraded to `needs_revision`.

## Why This Decision

- It gives users one predictable recovery path after manual Markdown edits.
- It keeps SQLite as the authority instead of introducing a second lifecycle source of truth.
- It prevents same-session self-approval in host review.
- It preserves auditability by forcing the import step to happen before revalidation.

## Alternatives Considered

### Auto-sync Markdown into SQLite on file save

Rejected because a file watcher would make lifecycle changes implicit and harder to audit.

### Treat Markdown as the authoritative lifecycle source

Rejected because the workflow already depends on revision history, stale propagation, and transition recording in SQLite.

### Re-run semantic review directly from edited Markdown without import

Rejected because it would let stale projections drive lifecycle decisions.

### Reuse the drafting session for host review

Rejected because it does not provide the required reviewer isolation.

## Consequences

- Manual Markdown edits can still create a temporary file/DB mismatch.
- The mismatch is now explicitly bounded and recoverable.
- Operators get a single command that both reconciles state and re-enters review.
- Host review is stronger because the reviewer context is fresh and packet-only.

## Notes

- `references/state-entrypoints.md` defines the state-entry contract.
- `references/cli-contract.md` defines the user-visible command behavior.
- `references/adr/0004-host-review-fresh-context-isolation.md` defines the host-review isolation requirement.
- `runbooks/review-resubmit.md` defines the operator recovery flow.
