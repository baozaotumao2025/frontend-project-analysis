# Downstream Commit Flow

Use this flow when a user has finished generating `fpa` analysis artifacts for a
downstream project and wants to commit them to their own repository.

## Flow

1. Identify the submission bundle.
   - Include the generated analysis files, `README.md`, `CHANGELOG.md`, and any
     project files that must change with them.
2. Decide the change type.
   - Use `analysis`, `sync`, `release`, `policy`, or `tooling`.
   - Do not force the change into the default `feat` / `fix` / `docs` / `chore`
     meanings.
3. Run the consistency checks.
   - Verify README, changelog, version metadata, and analysis artifacts still
     agree.
   - Confirm that every named command and file path still exists.
4. Confirm release readiness.
   - If the project uses a versioned release, make sure the version marker is
     updated everywhere it needs to be.
   - If the project uses a changelog, add or update the correct release entry.
5. Commit one coherent bundle.
   - Use a message like `sync(readme): align generated release guidance`.
6. Tag only when the project policy requires a release marker.
   - Tag the exact commit that contains the final bundle.
7. Push only after the working tree is clean.
   - Respect branch protection and any remote release policy.

## Practical Check List

- `README.md` still describes the current generated project behavior
- `CHANGELOG.md` reflects the intended version or release note
- Generated analysis artifacts still match the code and docs
- The commit type reflects the real change surface
- The repository is clean before push

If the submission contains both generated analysis changes and tool changes,
prefer one commit for the semantic bundle and a second commit only if the tool
change is independently understandable.

