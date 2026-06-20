# ADR 0007: Locale-Tolerant Cross-Reference Resolution

## Status

Accepted

## Context

The workflow artifacts are English-first in naming, but the documentation surface needs to stay usable for teams that write local-language labels, especially in Persona and cross-reference sections.

The previous structural checks treated cross-reference items as plain text labels with exact matching against slug or title.
That was deterministic, but it was too brittle for localized authoring and for Markdown-style links that are common in human-edited documents.

We want the validator to stay strict about identity while becoming more flexible about presentation.

## Decision

Structural cross-reference resolution MUST accept a small, explicit set of canonical forms:

- canonical artifact slug
- canonical artifact title
- frontmatter aliases declared on the target artifact
- Markdown link text or link target that resolves unambiguously to a known artifact

Canonical artifact identity remains the slug and artifact type in SQLite.
Localized labels are presentation forms, not new identities.
The validator MUST still fail unknown references so the workflow remains auditable.

The document templates should describe the accepted cross-reference forms so authors produce stable artifacts by default.

## Why This Decision

- It allows localized content without weakening workflow integrity.
- It avoids encoding special-case logic for any one language.
- It keeps the canonical database identity model stable.
- It gives authors a predictable way to write human-friendly documents while preserving machine validation.

## Alternatives Considered

### Keep exact text matching only

Rejected because it makes localized authoring unnecessarily fragile.

### Hardcode a separate locale table for every display language

Rejected because it adds configuration overhead without materially improving identity semantics.

### Accept arbitrary free-form labels

Rejected because it would weaken the validator and make false positives harder to detect.

## Consequences

- Page and Feature documents can use localized labels and Markdown links without tripping structural validation when the target is resolvable.
- Unknown references still fail fast.
- The resolver must continue to normalize whitespace and compare against canonical labels and declared aliases.
- Template guidance and tests must evolve together with the resolver so the accepted forms stay obvious.

## Notes

- `src/frontend_project_analysis/workflow/state/structural.py` implements the resolver.
- `references/templates.md` documents the accepted authoring forms.
- `tests/test_workflow_state_integrity.py` contains the positive and negative regression coverage.
