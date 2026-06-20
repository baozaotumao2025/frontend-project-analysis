# Downstream Project Commit Policy

This policy applies to projects generated with the `fpa` skill after the user
has produced analysis artifacts and wants to commit them to their own Git
repository.

It is not the release policy for the `frontend-project-analysis` skill
repository itself.

## Scope

Use this policy when the generated project contains human-edited analysis
artifacts such as `analysis/`, `README.md`, `CHANGELOG.md`, and project-specific
version metadata.

The goal is to keep the generated project internally consistent before commit,
tag, or push.

## Commit Bundle

Prefer to stage one coherent submission bundle at a time.

Typical bundle members include:

- `analysis/`
- `README.md`
- `CHANGELOG.md`
- `pyproject.toml` or the project-specific version file
- project code or scripts that were changed to match the generated analysis

Do not split a single semantic update across multiple commits unless the user is
intentionally making a follow-up cleanup commit.

## Consistency Rules

Before committing, verify:

1. `README.md` matches the current generated workflow and command surface.
2. `CHANGELOG.md` has a dated section for the intended version when the project
   is versioned.
3. The version source of truth matches across all version-bearing files.
4. Generated analysis artifacts still match the source code and the README
   claims.
5. Any document that names a command, file, or output path still refers to a
   real and current path.

If a project does not use a version file, replace the version check with the
project's chosen release marker.

## Commit Type Taxonomy

Do not use the default `feat` / `fix` / `docs` / `chore` meanings for these
projects.

Use the following generated-project types instead:

- `analysis`: changes to Personas, Story Maps, Page Maps, Features, GWT, or
  Feature Specs
- `sync`: changes that align README, changelog, generated analysis, or other
  project surfaces
- `release`: changes to version metadata, changelog release sections, tags, or
  release notes
- `policy`: changes to the rules that govern generated-project structure or
  workflow
- `tooling`: changes to scripts, automation, validation, or supporting command
  surfaces

## Commit Format

Use:

```text
<type>(<scope>): <summary>
```

Recommended scopes:

- `analysis`
- `readme`
- `changelog`
- `release`
- `workflow`
- `template`
- `tooling`

Examples:

```text
analysis(feature-spec): refine payment failure scenarios
sync(readme): align release instructions with generated scripts
release(version): bump to v1.3.3
policy(workflow): tighten output consistency checks
tooling(release): add publish validation script
```

## Push And Tag Readiness

Only push or tag when:

- the selected bundle is internally consistent
- any required review or inspection step has passed
- the working tree is clean after commit
- the tag points to the exact commit that produced the finalized bundle

If the project uses protected branches or release branches, follow the remote
policy first and the local convention second.

## Natural Language Routing

When a user asks in plain language, classify the request conservatively:

- Use `maintainer publish` when the user clearly asks to publish the skill
  repository itself.
- Use `downstream submit` when the user clearly asks to submit the generated
  project or current analysis bundle.
- Return no classification when the request is ambiguous, mixed, or missing the
  target repository context.

Do not infer a path from a single vague verb such as `publish` or `submit`
without a clear target.

The routing prompt itself follows the same template-driven pattern as the other
LLM prompt builders in `src/frontend_project_analysis/core/prompts.py`, and the
system and user prompt templates can be overridden through settings when the
caller needs project-specific phrasing.

The runnable LLM-managed router lives in `src/frontend_project_analysis/llm/submission.py`
and is exposed as `run_submission_intent`.
