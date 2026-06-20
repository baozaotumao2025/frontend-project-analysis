# Release Flow

Use this sequence when you are preparing a new git release for the repository.

Preferred one-shot launcher:

- `./scripts/release-publish.sh`
- `make release.publish`

The maintainer publish flow does the following in order:

1. Confirm the target version is new and consistent.
   - Keep `pyproject.toml`, `src/frontend_project_analysis/__init__.py`, and `CHANGELOG.md` in sync.
   - Do not reuse an existing tag for new work.
2. Run the release preflight checks.
   - `./scripts/release-preflight.sh`
3. Run the regression suite.
   - `./scripts/test-full.sh`
   - `./scripts/test-e2e.sh`
4. Run the fresh-session LLM review.
   - `./scripts/release-llm-review.sh`
   - Open a new reviewer session or fresh reviewer sub-agent and load only the generated packet.
   - If the review reports issues, fix them and rerun from step 2.
5. Validate release metadata.
   - Confirm `CHANGELOG.md` has a dated section for the target version.
   - Confirm `pyproject.toml` and `src/frontend_project_analysis/__init__.py` still match.
6. Create the release commit.
   - Stage the full release set.
   - Use a message like `chore(release): vX.Y.Z`.
7. Create an annotated tag for the same version.
   - Example: `git tag -a vX.Y.Z -m "vX.Y.Z"`
8. Verify the release state.
   - `git status --short` should be clean.
   - `git tag --list --sort=-creatordate | head -5` should show the new tag.
9. Push when the remote is ready.
   - Push the commit and tag together.
   - Respect branch protection and any remote release policy.
