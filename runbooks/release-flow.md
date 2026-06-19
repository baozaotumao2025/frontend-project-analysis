# Release Flow

Use this sequence when you are preparing a new git release for the repository.

1. Confirm the target version is new and consistent.
   - Keep `pyproject.toml`, `src/frontend_project_analysis/__init__.py`, and `README.md` in sync.
   - Do not reuse an existing tag for new work.
2. Run the release preflight checks.
   - `uv run pytest -q`
   - `uv run ruff check src/frontend_project_analysis tests`
   - `rg -n "/Users/cherubines/Documents/MaxCPA" README.md SKILL.md references frontend-decomposition-methodology.md AGENTS.md --glob '!references/release-checklist.md'`
   - `git status --short`
3. Fix any failures before committing.
   - Do not tag until tests and lint are green.
   - Do not include runtime state such as `.frontend-project-analysis/`.
4. Create the release commit.
   - Stage the full release set.
   - Use a message like `Release v1.2.0`.
5. Create an annotated tag for the same version.
   - Example: `git tag -a v1.2.0 -m "v1.2.0"`
6. Verify the release state.
   - `git status --short` should be clean.
   - `git tag --list --sort=-creatordate | head -5` should show the new tag.
7. Push when the remote is ready.
   - Push the commit and tag together.
   - Respect branch protection and any remote release policy.
