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

## Python Wheel

The installable Python package includes only:

- `src/frontend_project_analysis/`

## Release Shape Comparison

| Item | Repository Release Bundle | Python Wheel |
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
| `docs/` | Not included | Not included |
| `specs/` | Not included | Not included |

## Keep Local Only

- `.frontend-project-analysis/`
- `.env`
- `.venv/`
- `.pytest_cache/`
- `.ruff_cache/`
- `docs/`
- `specs/`
- `frontend-decomposition-methodology.md`

## Preflight Checks

Before publishing, verify:

1. `uv run pytest`
2. `uv run ruff check src/frontend_project_analysis tests`
3. `rg -n "/Users/cherubines/Documents/MaxCPA" README.md SKILL.md references frontend-decomposition-methodology.md AGENTS.md --glob '!references/release-checklist.md'` returns no matches
4. `git status --short` shows no runtime data such as `.frontend-project-analysis/`
   - The target project `.gitignore` includes `.frontend-project-analysis/`
5. `README.md`, `SKILL.md`, and `references/document-map.md` agree on document authority and reading order

## Release Notes

- `init` initializes the database automatically
- The published skill package should not contain runtime state or local analysis outputs
- If the release is intended for external use, confirm that version numbers in `pyproject.toml` and `src/frontend_project_analysis/__init__.py` match
