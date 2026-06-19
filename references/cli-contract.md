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
- `fpa review structural` remains the first gate that can move a `draft` artifact to `structurally_valid`.
- Beyond the structural gate, lifecycle changes only happen through `fpa review semantic-run`, `fpa review semantic-record`, `fpa review approve`, and `fpa review reject`.
- `fpa artifact link` can invalidate approval lineage when it introduces a new hard dependency.
- `fpa artifact ready` continues to report artifacts whose hard dependencies are approved, but it should be read as a scheduling hint, not a lifecycle override.

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
