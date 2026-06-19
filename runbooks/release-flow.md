# Release Flow

Use this sequence when you are preparing a new git release for the repository.

1. Confirm the target version is new and consistent.
   - Keep `pyproject.toml`, `src/frontend_project_analysis/__init__.py`, and `README.md` in sync.
   - Do not reuse an existing tag for new work.
2. Run the release preflight checks.
   - `./scripts/release.sh`
   - Or run `./scripts/release-preflight.sh` and `./scripts/release-llm-review.sh` separately if you need to pause between phases.
3. Fix any failures before committing.
   - Do not tag until the script passes and the docs/code/terminology audit is also `OK` or documented as an intentional `WARN`.
   - Do not include runtime state such as `.frontend-project-analysis/`.
4. Run the fresh-session LLM review.
   - `./scripts/release-llm-review.sh`
   - Open a new reviewer session and load only the generated packet.
   - If the review reports issues, fix them and rerun from step 2.
5. Create the release commit.
   - Stage the full release set.
   - Use a message like `Release v1.3.0`.
6. Create an annotated tag for the same version.
   - Example: `git tag -a v1.3.0 -m "v1.3.0"`
7. Verify the release state.
   - `git status --short` should be clean.
   - `git tag --list --sort=-creatordate | head -5` should show the new tag.
8. Push when the remote is ready.
   - Push the commit and tag together.
   - Respect branch protection and any remote release policy.
