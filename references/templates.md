# Templates

## Contents

- `docs/index.md`
- `docs/personas/index.md`
- `docs/personas/[persona-name].md`
- `docs/story-maps/[persona-name].md`
- `docs/pages/index.md`
- `docs/pages/[page-slug].md`
- `docs/features/[feature-name].md`
- `docs/gwt/[feature-name].feature`
- `specs/features/[feature-name]-spec.md`

`docs/index.md`

```md
# Documentation Index
```

`docs/personas/index.md`

```md
# Persona Index

| Persona | Core Goal | Story Map | Notes |
| --- | --- | --- | --- |
```

`docs/personas/[persona-name].md`

```md
# [Persona Name]

## Core Goal

## Key Differences From Other Persona

## Permission Boundary

## Invisible Pages Or Capabilities

## Related Documents
- Story Map: `../story-maps/[persona-name].md`
```

`docs/story-maps/[persona-name].md`

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

`docs/pages/index.md`

```md
# Page Index

| Route | Page Name | Accessible Persona | Responsibility |
| --- | --- | --- | --- |
```

`docs/pages/[page-slug].md`

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

`docs/features/[feature-name].md`

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

`docs/gwt/[feature-name].feature`

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
```

`specs/features/[feature-name]-spec.md`

```md
# [Feature Name] - Feature Spec

## Basic Information
## Roles And Permissions
## Component Breakdown
## State Boundary
### server state
### client state
## Cross-Feature Dependencies
## Given-When-Then Acceptance Spec
```
