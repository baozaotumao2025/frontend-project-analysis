# ADR 0008: LLM-Managed Submission Intent Routing

## Status

Accepted

## Context

This repository now serves two distinct submission scenarios:

- maintainer-facing publishing of the `frontend-project-analysis` skill repository
- downstream submission of generated project artifacts produced by users of the skill

Both scenarios may be initiated from natural language. Without an explicit routing layer, the two flows can be confused because they share surface verbs such as `submit`, `publish`, `push`, and `release`.

We also already have established LLM-managed flows in this repository:

- `brief assistant` uses prompt templates and settings overrides
- semantic review uses structured LLM providers and strict payload validation

The submission entrypoint should follow the same architectural pattern so that intent routing is centralized, testable, and configurable.

## Decision

We introduce a dedicated LLM-managed submission intent routing flow.

Specifically:

- `fpa submit` becomes the canonical natural-language entrypoint for submission routing.
- The router classifies a request into one of three intents:
  - `maintainer_publish`
  - `downstream_submit`
  - `ambiguous`
- The router uses a structured LLM payload when an external provider is configured, and a conservative local classifier for mock routing and tests.
- Prompt construction MUST use the same template-and-settings override pattern used by other LLM-assisted flows in this repository.
- The router MAY inspect repository context, but it MUST remain conservative when the request does not clearly identify the target repository or action.
- The router only decides which workflow should run next; it does not execute the publish or submission side effects itself.

This ADR intentionally separates routing from policy:

- `references/downstream-commit-policy.md` defines what a valid downstream submission bundle looks like.
- this ADR defines how a natural-language request is routed to the correct submission path.

## Alternatives Considered

### Keep the two submission flows implicit and rely on user wording

Rejected because the same verbs can refer to different targets, and the ambiguity would leak into operator behavior.

### Add a command for each path and remove natural-language routing

Rejected because it would be harder to use and would diverge from the existing LLM-assisted entrypoint pattern.

### Hard-code routing rules without prompt templates or settings overrides

Rejected because that would duplicate logic and make the router inconsistent with `brief assistant` and semantic review.

### Merge maintainer publishing and downstream submission into one policy

Rejected because the two scenarios have different authorities, file bundles, and release semantics.

## Consequences

- Users can invoke a single natural-language command and still reach the correct workflow.
- The repository now has a shared routing surface for future LLM-assisted entrypoints.
- Tests must cover both positive and negative routing cases, including ambiguous requests.
- Prompt changes can be made centrally through settings overrides instead of editing the command implementation.
- Documentation must continue to distinguish routing from downstream submission policy so the two concerns do not blur together.

## Notes

- `src/frontend_project_analysis/commands/submit.py` implements the CLI entrypoint.
- `src/frontend_project_analysis/core/prompts.py` and `src/frontend_project_analysis/core/config.py` hold the configurable prompt templates.
- `src/frontend_project_analysis/llm/submission.py` implements the structured LLM routing flow.
- `references/downstream-commit-policy.md` remains the canonical policy for generated-project submission.
