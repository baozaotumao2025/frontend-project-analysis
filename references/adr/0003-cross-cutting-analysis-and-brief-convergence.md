# ADR 0003: Cross-Cutting Analysis And Brief Convergence

## Status

Accepted

## Context

The workflow already decomposes a product into `Persona` -> `Story Map` -> `Page` -> `Feature` -> `GWT` -> `Feature Spec`.

That main chain is strong for business decomposition, but by itself it can still leave important cross-cutting concerns implicit:

- `discovery` and `evidence`
- `risk` and `assumption`
- `accessibility`
- `observability`
- `release`
- `compliance`

We also want a better entry path for users who do not yet have a polished brief. The current `brief interview` command is useful as a bounded Q&A flow, but it should do more than collect three high-level answers. It should converge a `project brief` that already carries the most important cross-cutting signals forward into `init` and the downstream rounds.

We need to improve this without breaking the existing six-round structure or forcing every project to answer irrelevant questions.

## Decision

We keep the six-round decomposition as the core workflow, and add a cross-cutting layer that travels through the same rounds when relevant.

Specifically:

- `brief interview` becomes a bounded convergence helper for a user-owned `project brief`.
- The generated brief should preserve the main product description plus the most relevant cross-cutting signals.
- `Feature Spec` becomes the primary place where discovery evidence, risks, assumptions, accessibility, observability, release, and compliance are made explicit when they affect delivery.
- Structural and semantic validation should enforce those concerns when the project context makes them relevant.

We keep the new layer aligned with the existing workflow instead of introducing separate analysis rounds.

## Why this decision

- It preserves the simplicity of the current six-round mental model.
- It makes the brief more useful as a real project input, not just a short summary.
- It keeps important delivery concerns visible before implementation begins.
- It gives the reviewer and the CLI something concrete to enforce.
- It avoids making every project carry the same amount of overhead when a concern is not relevant.

## Alternatives Considered

### Keep the existing six rounds unchanged and leave cross-cutting concerns implicit

Rejected because important delivery risks, accessibility expectations, and release constraints can disappear between the brief and the implementation plan.

### Add new dedicated rounds for discovery, risk, accessibility, observability, and release

Rejected because that would make the workflow heavier and less usable. These concerns are important, but they are better treated as signals that flow through the existing rounds.

### Make the brief interview ask a huge fixed questionnaire for every project

Rejected because it would make the helper noisy and slow, and many projects do not need every concern to be expanded equally.

## Consequences

- The `project brief` becomes a richer input to `init`.
- `Feature Spec` documents become more complete and more operationally useful.
- Quality gates become stricter where cross-cutting concerns matter.
- The CLI and tests need to enforce the richer shape, not just document it.
- The workflow remains a six-round system, so adoption stays manageable.

## Notes

- `references/methodology.md` defines the main round structure and the cross-cutting coverage rule.
- `references/quality-gates.md` defines the new validation expectations.
- `references/glossary.md` defines the vocabulary for the new cross-cutting terms.
- `references/templates.md` defines the expected shape of brief, GWT, and Feature Spec documents.
- `src/frontend_project_analysis/commands/brief.py` implements the convergence helper.
