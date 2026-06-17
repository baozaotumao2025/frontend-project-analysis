# Workflow

## Round 1: Persona Definition

- Input: project description
- Output: `docs/personas/index.md` and `docs/personas/[persona-name].md`
- Each Persona should include name, core goal, key differences, permission boundary, and invisible pages or capabilities
- Before approval, register or import the resulting artifacts into the SQLite workflow state

Persona split rules:

- Split into separate Persona only when goals, decisions, or core paths truly differ
- If the path is the same and only permissions differ, keep one Persona and explain the permission boundary

## Round 2: Story Map

- Input: approved `docs/personas/*.md`
- Output: `docs/story-maps/index.md` and `docs/story-maps/[persona-name].md`
- One Story Map per Persona
- Format: `Activity -> Step -> Story`
- Do not mention pages or Features
- Semantic review should judge business coherence; structural review still runs via CLI

## Round 3: Page Mapping

- Input: approved `docs/story-maps/*.md`
- Output: `docs/pages/index.md`, `docs/pages/[page-slug].md`, and `docs/relations/persona-story-page-matrix.md`
- Map Story Steps into page, modal, drawer, or tab surfaces

## Round 4: Feature Slicing

- Input: approved `docs/pages/*.md`
- Output: `docs/features/index.md`, `docs/features/[feature-name].md`, and `docs/relations/feature-coverage-matrix.md`
- Process 1-3 pages at a time, then pause
- Each Feature should record name, page, responsibility, state type, and cross-page reuse

## Round 5: Given-When-Then

- Input: approved `docs/features/*.md`
- Output: `docs/gwt/[feature-name].feature`
- Process one Feature at a time, then pause

## Round 6: Feature Spec

- Input: all approved artifacts
- Output: `specs/features/[feature-name]-spec.md`
- Generate one Feature Spec per Feature
- Final release planning should rely on recorded dependency edges and approval state, not on manual matrix edits alone
