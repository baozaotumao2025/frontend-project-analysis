# Release Checklist

This checklist defines what should be included in a public skill release and what must stay local.

## Repository Release Bundle

- `SKILL.md`
- `README.md`
- `references/`
- `agents/openai.yaml`
- `pyproject.toml`
- `src/frontend_project_analysis/`
- `migrations/`
- `scripts/`
- `tests/`

## Python Package

The published Python package includes only:

- `src/frontend_project_analysis/`

## Release Shape Comparison

| Item | Repository Release Bundle | Python Package |
| --- | --- | --- |
| `SKILL.md` | Included | Not included |
| `README.md` | Included | Not included |
| `references/` | Included | Not included |
| `agents/openai.yaml` | Included | Not included |
| `pyproject.toml` | Included | Not included |
| `src/frontend_project_analysis/` | Included | Included |
| `migrations/` | Included | Not included |
| `scripts/` | Included | Not included |
| `tests/` | Included | Not included |
| `.frontend-project-analysis/` | Not included | Not included |
| `.env` | Not included | Not included |
| `analysis/` | Not included | Not included |

## Keep Local Only

- `.frontend-project-analysis/`
- `.env`
- `.venv/`
- `.pytest_cache/`
- `.ruff_cache/`
- `analysis/`
- `frontend-decomposition-methodology.md`

## Preflight Checks

Before publishing, verify:

1. `./scripts/release-preflight.sh`
2. `./scripts/release-llm-review.sh` and a fresh reviewer session or sub-agent complete the semantic review
3. `git status --short` shows no runtime data such as `.frontend-project-analysis/`
   - The target project `.gitignore` includes `.frontend-project-analysis/`
4. `README.md`, `SKILL.md`, and `references/document-map.md` agree on document authority and reading order
5. Run the docs/code/terminology audit in [`runbooks/release-doc-audit.md`](../runbooks/release-doc-audit.md)
   - Confirm every public behavior changed in code has a matching description update
   - Confirm every public claim changed in a description file has a matching code path, test, or workflow rule
   - Confirm `references/glossary.md` still owns the vocabulary used by the release

## Capability Readiness Criteria

Use these checks to decide whether the `Formal mode` / `Explore mode` capability is ready to ship:

- `workflow start` still hard-blocks when the formal upstream round is not `approved` and fresh
- `workflow explore start` succeeds for the same draft or unapproved upstream inputs without mutating canonical lifecycle state
- `workflow --help` and `workflow explore --help` expose the discoverable entrypoints
- The focused regression set passes:
  - `tests/test_cli_workflow_gate.py`
  - `tests/test_cli_smoke.py`
  - `tests/test_cli_e2e.py`
- The documentation set is aligned:
  - `README.md`
  - `references/workflow.md`
  - `references/cli-contract.md`
  - `references/state-entrypoints.md`
  - `runbooks/test-matrix.md`
  - `references/adr/0006-formal-and-explore-workflow-modes.md`
- The release audit reports no untracked mismatch for the new commands or terminology
- The formal round gate behavior and stale propagation behavior remain unchanged for canonical delivery
- Any host-mode packet review continues to require a fresh reviewer sub-agent when Codex sub-agents are available

## Docs And Terminology Audit

This audit is the fixed release gate for code/document parity.

- If a changed code file affects a public command, workflow rule, or exported artifact, update the matching description file before release.
- If a changed description file states a behavior that code does not implement, either update the code or mark the description as intentional future work.
- If a new domain term appears, add it to `references/glossary.md` before reusing it elsewhere.
- If a term in `references/glossary.md` is English-only, keep that spelling unchanged in all release-facing files.

## Preferred Launcher

- Use `./scripts/release.sh` or `make release` for the combined preflight plus packet-generation path.
- Use `./scripts/release-preflight.sh` and `./scripts/release-llm-review.sh` separately only when you need to pause between phases.

## Release Notes

- `init` initializes the database automatically
- The published skill package should not contain runtime state or local analysis outputs
- If the release is intended for external use, confirm that version numbers in `pyproject.toml` and `src/frontend_project_analysis/__init__.py` match
- For the preferred git commit and tagging sequence, see [`runbooks/release-flow.md`](../runbooks/release-flow.md)
- For the preferred testing matrix, see [`runbooks/test-matrix.md`](../runbooks/test-matrix.md)
