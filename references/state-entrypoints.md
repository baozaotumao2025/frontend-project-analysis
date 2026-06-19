# State Entrypoints

This page lists the commands that can mutate workflow state and the ones that are read-only.

## Source Of Truth

- The SQLite workflow database is the authoritative state store.
- Markdown files, manifests, and CLI prompts are inputs or projections, not lifecycle authority by themselves.
- Any command that changes revision state must go through the code-enforced transition layer.

## Write Entrypoints

These commands can create or mutate workflow state:

| Command | State Effect | Notes |
| --- | --- | --- |
| `fpa install` | Installs the reusable project scaffold into the current repo | Idempotent by default; supports `--force` and `--dry-run` |
| `fpa init` | Installs the scaffold and bootstraps the project database and docs layout | Composite entrypoint for a fresh repo; supports `--force` and `--dry-run` |
| `fpa db init` | Initializes or migrates the workflow database | Safe to run on a fresh target root |
| `fpa db wipe --yes` | Deletes the workflow database file | Destructive; use only when you intend to reset state |
| `fpa project init` | Initializes the database and bootstraps the project scaffold | Compatibility alias for `fpa init`; requires `alembic.ini`, `migrations/`, and importable `src/` in the repo root; also ensures `.frontend-project-analysis/` is ignored by the target project's `.gitignore` |
| `fpa project install` | Installs the reusable scaffold files only | Lower-level alias for `fpa install` |
| `fpa artifact add` | Creates a new `draft` revision only | Pre-approved creation is rejected |
| `fpa artifact link` | Writes dependency edges | May mark approved downstream revisions `stale` when a new hard dependency is introduced |
| `fpa import manifest --apply` | Imports artifacts and dependencies as draft-state revisions | Inbound `status` values are ignored as lifecycle overrides |
| `fpa import markdown-scan --apply` | Synchronizes documents into draft-state revisions | Inbound frontmatter `status` is ignored |
| `fpa review structural` | Moves eligible revisions to `structurally_valid` | Can also be used to revalidate `stale` revisions |
| `fpa review semantic-run` | Records semantic review and advances state according to the review result | May stop at `semantic_review` when human approval is still required |
| `fpa review semantic-record` | Records an externally produced semantic review result | Same state effect as `semantic-run` record mode |
| `fpa review approve` | Moves a `semantic_review` revision to `approved` | Also propagates freshness invalidation through dependents when needed |
| `fpa review reject` | Moves a revision to `rejected` | Ends the current revision's approval path |

## Gate Entrypoints

These commands check state and do not mutate it:

| Command | Purpose |
| --- | --- |
| `fpa workflow gate` | Diagnostic gate check for a target round |
| `fpa workflow start` | Hard gate that must pass before a downstream round continues |

## Read-Only Entrypoints

These commands read state or export projections without changing lifecycle status:

| Command | Purpose |
| --- | --- |
| `fpa artifact ready` | Reports artifacts that are ready for scheduling |
| `fpa export manifest` | Exports the current artifact graph snapshot |
| `fpa export relations` | Exports relationship matrices and coverage views |
| `fpa db backup` | Copies the current database for recovery or inspection |
| `fpa db restore` | Replaces the current database with a backup copy |

## Operator Rules

- If a user changes their mind in plain language, the assistant must translate that into one of the write entrypoints above.
- If a command path is not one of the listed write entrypoints, it must not be treated as a state mutation.
- If a revision becomes `stale`, the next round gate must re-check freshness before any downstream work continues.
