# ADR 0002: Document Layering And Rule Placement

## Status

Accepted

## Context

The repository contains both a user-facing summary and a canonical reference layer.

We need a stable place for:

- high-level project overview
- workflow and lifecycle rules
- architectural rationale for important decisions

If these concerns are mixed into `README.md`, the file becomes harder to scan and easier to drift. If they are not separated, the project loses a clear source of truth.

## Decision

We separate documentation into three layers:

- `README.md` stays a summary and entry point.
- `references/*.md` holds canonical rules, contracts, semantics, and operational guidance.
- `references/adr/*.md` holds durable decision rationale for architecturally significant choices.

We do not place the workflow gate model or rollback rationale in `README.md`.

## Alternatives Considered

### Put all rules in `README.md`

Rejected because the file would become too dense and would mix overview with policy.

### Keep rules only in code comments

Rejected because the rules need to be discoverable and reviewable outside the implementation.

### Skip ADRs and rely only on reference docs

Rejected because important decisions need rationale, not only current rules.

## Consequences

- Readers can find the project overview quickly.
- Canonical rules remain in the reference layer.
- Decision history is preserved separately from the rule statements themselves.

## Notes

- `references/document-map.md` is the authoritative index for document responsibility.
- `references/repo-layers.md` explains how the layers relate.
- `references/adr/index.md` indexes the rationale records.
