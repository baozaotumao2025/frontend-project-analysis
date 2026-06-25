# Templates

## Contents

- `analysis/index.md`
- `analysis/brief.md` (copied from user-provided confirmed brief input)
- `analysis/personas/index.md`
- `analysis/personas/[persona-name].md`
- `analysis/story-maps/[persona-name].md`
- `analysis/pages/index.md`
- `analysis/pages/[page-slug].md`
- `analysis/features/index.md`
- `analysis/features/[feature-name].md`
- `analysis/relations/index.md`
- `analysis/relations/persona-story-page-matrix.md`
- `analysis/relations/feature-coverage-matrix.md`
- `analysis/gwt/[feature-name].feature`
- `analysis/relations/gwt-feature-matrix.md`
- `analysis/relations/graph.html`
- `analysis/specs/features/[feature-name]-spec.md`

`analysis/index.md`

```md
# Analysis Index
```

`analysis/brief.md` is not a synthetic template; it is the copied, confirmed project brief supplied by the user.

```md
# Project Brief
```

`analysis/personas/index.md`

```md
# Persona Index

| Persona | Core Goal | Story Map | Notes |
| --- | --- | --- | --- |
```

`analysis/personas/[persona-name].md`

```md
# [Persona Name]

## Core Goal

## Key Differences From Other Persona

## Permission Boundary

## Invisible Pages Or Capabilities

## Related Documents
- Story Map: `../story-maps/[persona-name].md`
```

`analysis/story-maps/[persona-name].md`

```md
# [Persona Name] Story Map

## Start
- []

## Activity 1: []
- Step 1: []
  - Story: []

## End
- []
```

`analysis/pages/index.md`

```md
# Page Index

| Route | Page Name | Accessible Persona | Responsibility |
| --- | --- | --- | --- |
```

`analysis/pages/[page-slug].md`

```md
# [Page Name]

## Route Information
- Route: `...`

## Accessible Persona
- []

## Story Steps Covered
- []

## Page Responsibility

## Related Features
- []
```

Cross-reference items in `## Accessible Persona` and `## Related Features` should prefer canonical artifact labels.
If a localized display label is needed, keep it as a frontmatter alias or use a Markdown link whose display text is localized
but whose target still resolves to a known artifact.

`analysis/features/[feature-name].md`

```md
# [Feature Name]

## Page

## Persona Served

## Business Responsibility

## State Type

## Cross-Page Reuse

## Source Story
- []
```

Cross-reference items in `## Page` and `## Persona Served` should prefer canonical labels or frontmatter aliases.
Avoid inventing free-form labels that do not map back to an existing artifact.
Markdown links are allowed when the display text or target can still be resolved unambiguously.

`analysis/gwt/[feature-name].feature`

```yaml
---
artifact_type: gwt
slug: [feature-name]
round: 5
status: draft
project: [project-key]
feature: [feature-name]
title: [Feature Name]
---
```

```gherkin
Feature: [feature-name]

  Scenario: Happy Path
    Given []
    When []
    Then []

  Scenario: Permission Case
    Given []
    When []
    Then []

  Scenario: Error Case
    Given []
    When []
    Then []

  Scenario: Edge Case
    Given []
    When []
    Then []

  Scenario: Accessibility Case
    Given []
    When []
    Then []
```

`analysis/relations/gwt-feature-matrix.md`

```md
# GWT Feature Matrix

| GWT | Feature | Page | Persona | Story Map |
| --- | --- | --- | --- | --- |
```

`analysis/relations/index.md`

```md
# Relations Index

## Matrices

- [Persona Story Page Matrix](./persona-story-page-matrix.md)
- [Feature Coverage Matrix](./feature-coverage-matrix.md)
- [GWT Feature Matrix](./gwt-feature-matrix.md)

## Graph Views

- [Relationship Graph](./graph.html)
```

`analysis/relations/persona-story-page-matrix.md`

```md
# Persona Story Page Matrix

| Persona | Story Map | Page | Feature | GWT |
| --- | --- | --- | --- | --- |
```

`analysis/relations/feature-coverage-matrix.md`

```md
# Feature Coverage Matrix

| Feature | Persona | Page | Story Map | GWT |
| --- | --- | --- | --- | --- |
```

`analysis/specs/features/[feature-name]-spec.md`

```md
# [Feature Name] - Feature Spec

## Basic Information
## Discovery And Evidence
## Risks And Assumptions
## Roles And Permissions
## Component Breakdown
## State Boundary
### server state
### client state
## Accessibility
## Observability
## Release And Compliance
## Cross-Feature Dependencies
## Given-When-Then Acceptance Spec
```
