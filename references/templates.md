# Templates

## Contents

- `analysis/index.md`
- `analysis/brief.md` (copied from user-provided brief input)
- `analysis/personas/index.md`
- `analysis/personas/[persona-name].md`
- `analysis/story-maps/[persona-name].md`
- `analysis/pages/index.md`
- `analysis/pages/[page-slug].md`
- `analysis/features/[feature-name].md`
- `analysis/gwt/[feature-name].feature`
- `analysis/specs/features/[feature-name]-spec.md`

`analysis/index.md`

```md
# Analysis Index
```

`analysis/brief.md` is not a synthetic template; it is the copied project brief supplied by the user.

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

`analysis/gwt/[feature-name].feature`

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
