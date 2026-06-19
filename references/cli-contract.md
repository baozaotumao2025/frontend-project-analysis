# CLI Contract Under State Gates

This page summarizes the user impact of the code-enforced state gates.

## What Changed

- Artifact lifecycle entry is now code-enforced instead of document-only.
- New artifacts and imported artifacts always start as `draft`.
- Lifecycle advancement only happens through review commands or controlled transition paths.
- Content changes can downgrade an artifact to `draft` or `stale` when freshness is lost.

## User Impact

- `artifact add` no longer supports creating a pre-approved artifact.
- `import manifest` and `import markdown-scan` no longer trust imported `status` as a lifecycle override.
- If an approved artifact changes, the user must re-run the round gates before continuing downstream work.
- If a new hard dependency is added to an approved artifact, downstream approved artifacts can become `stale` and need revalidation.

## CLI Impact

- `fpa artifact add` is now a draft-only registration command.
- `fpa workflow start` hard-checks that a downstream round can start only after the required upstream revisions are approved and fresh.
- `fpa workflow start --mode explore` allows the user to inspect later-round analysis against draft or unapproved upstream material without promoting that material into canonical lifecycle state.
- `fpa workflow explore start` is the discoverable exploratory entrypoint and behaves like `--mode explore`.
- `fpa review structural` remains the first gate that can move a `draft` artifact to `structurally_valid`.
- Beyond the structural gate, lifecycle changes only happen through `fpa review semantic-run`, `fpa review semantic-record`, `fpa review approve`, and `fpa review reject`.
- `fpa review resubmit` is the operator-facing fast path for Markdown edits and stale revisions; it re-imports the target workspace, reruns structural review, and then either completes semantic review or exports a fresh host packet for a reviewer sub-agent.
- `host` semantic review MUST use a fresh reviewer context; in Codex environments this means a sub-agent with `fork_context: false`. If the output lacks counterexamples or evidence, code will downgrade it to `needs_revision`.
- `fpa artifact link` can invalidate approval lineage when it introduces a new hard dependency.
- `fpa artifact ready` continues to report artifacts whose hard dependencies are approved, but it should be read as a scheduling hint, not a lifecycle override.
- After a manual Markdown edit, SQLite and the file tree may diverge until `import markdown-scan --apply` or `review resubmit` runs; that transient mismatch is expected and must be resolved by re-import before downstream review or gate decisions continue.

## Related Files

- [`src/frontend_project_analysis/repositories/versions.py`](../src/frontend_project_analysis/repositories/versions.py)
- [`src/frontend_project_analysis/repositories/dependencies.py`](../src/frontend_project_analysis/repositories/dependencies.py)
- [`src/frontend_project_analysis/workflow/state/gates.py`](../src/frontend_project_analysis/workflow/state/gates.py)
- [`src/frontend_project_analysis/workflow/state/transitions.py`](../src/frontend_project_analysis/workflow/state/transitions.py)
- [`src/frontend_project_analysis/workflow/io/import_manifest.py`](../src/frontend_project_analysis/workflow/io/import_manifest.py)
- [`src/frontend_project_analysis/workflow/io/import_markdown.py`](../src/frontend_project_analysis/workflow/io/import_markdown.py)
- [`references/state-entrypoints.md`](state-entrypoints.md)
- [`src/frontend_project_analysis/commands/artifact/add.py`](../src/frontend_project_analysis/commands/artifact/add.py)
- [`src/frontend_project_analysis/commands/artifact/link.py`](../src/frontend_project_analysis/commands/artifact/link.py)

## Operational Notes

- `init` still needs the repository root to expose `alembic.ini`, `migrations/`, and importable `src/`.
- The workflow is intentionally conservative: when in doubt, reset to `draft` or `stale` and force the next round gate to re-validate freshness.
- This keeps approval history auditable and avoids silently rewriting downstream work.
