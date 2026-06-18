# Structure

## Recommended Output Layout

```text
docs/
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
    persona-story-page-matrix.md
    feature-coverage-matrix.md
  gwt/
    [feature-name].feature
specs/
  features/
    [feature-name]-spec.md
```

## Naming Rules

- Persona files: semantic kebab-case such as `finance-manager.md`
- Story Map files: same base name as the Persona file
- Page files: semantic kebab-case such as `customer-detail.md`
- Feature files: semantic kebab-case such as `customer-assignment.md`
- GWT files: same base name as the Feature file with `.feature`
- Spec files: same base name as the Feature file with `-spec.md`

## Responsibility Boundaries

- `docs/personas/[persona-name].md`: Persona definition only
- `docs/story-maps/[persona-name].md`: `Activity -> Step -> Story` only
- `docs/pages/[page-slug].md`: page scope, accessible Persona, Story Steps, page responsibility, related Features
- `docs/features/[feature-name].md`: Feature summary with page, Persona, responsibility, state type, reuse, and source story
- `docs/relations/persona-story-page-matrix.md`: Persona to Story to Page to Feature mapping
- `docs/relations/feature-coverage-matrix.md`: Feature to Persona, Page, and Story mapping
- `docs/gwt/[feature-name].feature`: acceptance behavior
- `specs/features/[feature-name]-spec.md`: implementation boundary and detail

## Managed Frontmatter

Structured Markdown artifact files that participate in workflow state should include frontmatter like:

```yaml
---
artifact_type: feature
slug: customer-assignment
round: 4
status: draft
project: crm-web
title: Customer Assignment
---
```

The CLI validates these fields during structural review for Persona, Story Map, Page, and Feature artifacts.

## Design Rules

- One Markdown file should describe either one entity or one relationship view
- Relationship-dense information belongs in index or matrix files
- Prefer progressive disclosure: index first, entity files second, acceptance and spec detail last
- Keep core professional terms in English
