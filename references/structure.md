# Structure

## Scope

This document defines the default output layout and file responsibility boundaries for the `fpa` workflow.

- It is a canonical reference for generated analysis artifacts.
- It is not the place for repository-wide governance rules.
- It is not the place for operational runbook steps.

## Recommended Output Layout

```text
analysis/
  index.md
  personas/
    index.md
    [persona-name].md
  story-maps/
    index.md
    [persona-name].md
  pages/
    index.md
    [page-slug].md
  features/
    index.md
    [feature-name].md
  relations/
    index.md
    persona-story-page-matrix.md
    feature-coverage-matrix.md
    gwt-feature-matrix.md
    graph.html
  gwt/
    [feature-name].feature
  brief.md
  specs/
    features/
      [feature-name]-spec.md
```

`analysis/brief.md` is copied from a user-provided, confirmed project brief and is not auto-generated from a placeholder.

Cross-reference sections may use canonical labels, localized aliases declared in frontmatter `aliases`, or Markdown links whose display text or target resolves to a known artifact.

## Naming Rules

- Persona files: semantic kebab-case such as `finance-manager.md`
- Story Map files: same base name as the Persona file
- Page files: semantic kebab-case such as `customer-detail.md`
- Feature files: semantic kebab-case such as `alpha-feature.md`
- GWT files: same base name as the Feature file with `.feature`
- Spec files: same base name as the Feature file with `-spec.md`

## Responsibility Boundaries

- `analysis/personas/[persona-name].md`: Persona definition only
- `analysis/story-maps/[persona-name].md`: `Activity -> Step -> Story` only
- `analysis/pages/[page-slug].md`: page scope, accessible Persona, Story Steps, page responsibility, related Features
- `analysis/features/[feature-name].md`: Feature summary with page, Persona, responsibility, state type, reuse, and source story
- `analysis/relations/index.md`: entrypoint for matrix and graph relationship views
- `analysis/relations/persona-story-page-matrix.md`: `Persona | Story Map | Page | Feature | GWT`
- `analysis/relations/feature-coverage-matrix.md`: `Feature | Persona | Page | Story Map | GWT`
- `analysis/relations/gwt-feature-matrix.md`: `GWT | Feature | Page | Persona | Story Map`
- `analysis/relations/graph.html`: interactive artifact relationship graph rendered from exported graph data
- `analysis/gwt/[feature-name].feature`: acceptance behavior with explicit Feature binding
- `analysis/specs/features/[feature-name]-spec.md`: implementation boundary, discovery evidence, risk, accessibility, observability, release/compliance, and delivery detail

## Managed Frontmatter

Structured Markdown artifact files that participate in workflow state should include frontmatter like:

```yaml
---
artifact_type: feature
slug: alpha-feature
round: 4
status: draft
project: crm-web
title: Alpha Feature
---
```

The CLI validates these fields during structural review for Persona, Story Map, Page, Feature, and GWT artifacts.
The file body remains the human-edited artifact content, while the database owns lifecycle and dependency state. Hand edits to the file still need import reconciliation before downstream workflow can trust them.

## Design Rules

- One Markdown file should describe either one entity or one relationship view
- Relationship-dense information belongs in index or matrix files
- Prefer progressive disclosure: index first, entity files second, acceptance and spec detail last
- Do not hand-edit matrix files as if they were primary records; regenerate them from the database
- Keep core professional terms in English
