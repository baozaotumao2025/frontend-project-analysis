# State Entrypoints

This page lists the commands that can mutate workflow state and the ones that are read-only.

## Source Of Truth

- The SQLite workflow database is the authoritative state store.
- Markdown files, manifests, and CLI prompts are inputs or projections, not lifecycle authority by themselves.
- Direct Markdown edits are allowed as authoring input, but they are not canonical until `fpa import markdown-scan --apply` reconciles them into the database.
- Any command that changes revision state must go through the code-enforced transition layer.

## Preflight Helper

These commands help prepare inputs before workflow state is initialized, but they do not mutate the workflow database:

| Command | Purpose | Notes |
| --- | --- | --- |
| `fpa brief interview` | Collects a user-owned project brief in a bounded Q&A flow | Use `--transcript` to keep the conversation log; the output is a draft brief and must be confirmed before `fpa init` |
| `fpa brief assistant` | Collects a user-owned project brief with LLM-assisted follow-up and synthesis | Use `--transcript` to keep the conversation log; the output is a draft brief and must be confirmed before `fpa init` |
| `fpa brief confirm` | Marks a draft brief as confirmed and verifies its provenance metadata | Use `--input` for the draft brief, and `--output` when you want to write a separate confirmed copy |

## Write Entrypoints

These commands can create or mutate workflow state:

| Command | State Effect | Notes |
| --- | --- | --- |
| `fpa init` | Bootstraps the project database and analysis workspace from confirmed brief input | Composite entrypoint for a fresh repo; requires `--brief` or `--brief-file` containing confirmed brief metadata, and supports `--force` and `--dry-run` |
| `fpa db init` | Initializes or migrates the workflow database | Safe to run on a fresh target root |
| `fpa db wipe --yes` | Deletes the workflow database file | Destructive; use only when you intend to reset state |
| `fpa project init` | Initializes the database and analysis workspace | Alias for `fpa init`; requires confirmed brief input and ensures `.frontend-project-analysis/` is ignored by the target project's `.gitignore` |
| `fpa artifact add` | Creates a new `draft` revision only | Pre-approved creation is rejected |
| `fpa artifact link` | Writes dependency edges | May mark approved downstream revisions `stale` when a new hard dependency is introduced |
| `fpa import manifest --apply` | Imports artifacts and dependencies as draft-state revisions | Inbound `status` values are ignored as lifecycle overrides |
| `fpa import markdown-scan --apply` | Reconciles Markdown changes into draft-state revisions | Inbound frontmatter `status` is ignored; this does not make Markdown a second source of lifecycle truth |
| `fpa review structural` | Moves eligible revisions to `structurally_valid` | Can also be used to revalidate `stale` revisions |
| `fpa review semantic-run` | Records semantic review and advances state according to the review result | May stop at `semantic_review` when human approval is still required |
| `fpa review semantic-record` | Records an externally produced semantic review result | Same state effect as `semantic-run` record mode |
| `fpa review resubmit` | Reconciles Markdown edits, reruns structural review, and continues semantic review or packet handoff | Accepts `stale`, `draft`, `rejected`, `structurally_valid`, `semantic_review`, and `approved` revisions when they need revalidation |
| `fpa review approve` | Moves a `semantic_review` revision to `approved` | Also propagates freshness invalidation through dependents when needed |
| `fpa review reject` | Moves a revision to `rejected` | Ends the current revision's approval path |

## Gate Entrypoints

These commands check state and do not mutate it:

| Command | Purpose |
| --- | --- |
| `fpa workflow gate` | Diagnostic gate check for a target round |
| `fpa workflow start` | Hard gate that must pass before a downstream round continues |
| `fpa workflow explore gate` | Exploratory gate check that allows draft or unapproved upstream material |
| `fpa workflow explore start` | Exploratory start check that allows draft or unapproved upstream material |

`fpa workflow gate` and `fpa workflow start` both accept `--mode formal` for canonical delivery and `--mode explore` for local analysis against draft or otherwise unapproved upstream material. `Explore mode` does not mutate canonical lifecycle state and must not be treated as approval.

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
- If a user edits Markdown by hand, the assistant should treat the database as stale until the relevant import command runs.
- If a command path is not one of the listed write entrypoints, it must not be treated as a state mutation.
- If a revision becomes `stale`, the next round gate must re-check freshness before any downstream work continues.
