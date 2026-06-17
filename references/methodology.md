# Frontend Decomposition Methodology

## Contents

- Round 1: Define Persona
- Round 2: Story Map
- Round 3: Page Map
- Round 4: Feature Slicing
- Round 5: Given-When-Then
- Round 6: Feature Spec And Delivery Planning
- Workflow Summary

## 6-Round Conversation Workflow

## Round 1: Define Persona

Input: project description

Target artifact: a Persona card table with role, core goal, permission boundary, and invisible pages

```text
You are a senior frontend product architect.

## Task
Based on the following project description, complete the first step: define user Persona.

## Project Description
[Paste the project description, including product goals, user groups, and core scenarios]

## Output Requirements
Use a Markdown table. Each Persona must include:
- Persona name
- Core goal
- Key difference from other Persona
- Permission boundary
- Pages or capabilities that are not visible

Do not output flows, pages, or features. Only output Persona definitions.
```

## Round 2: Story Map

Input: confirmed Round 1 output

Target artifact: a Story Map for each Persona using `Activity -> Step -> Story`

```text
Based on the confirmed Persona below:

[Paste the Round 1 output]

## Task
Create a User Story Map for each Persona.

## Output Requirements
- One Story Map per Persona
- Format: Activity -> Step -> Story
- Use a tree-like code block format
- Describe user behavior only
- Do not mention page names or feature names
- Keep each Activity within 5 Steps

Do not output routes, components, or state management details.
```

## Round 3: Page Map

Input: confirmed Round 2 output

Target artifact: route tree, page list, and Persona-to-page mapping

```text
Based on the confirmed Story Map below:

[Paste the Round 2 output]

## Task
Map Story Map steps into pages.

## Mapping Rules
- A distinct route becomes a distinct page
- Contextual actions without navigation should be marked as modal, drawer, or tab
- Multiple steps on the same page should be merged
- Shared pages across Persona should appear once and list all accessible Persona

## Output Requirements
1. A route tree in a code block with route path and page name
2. A page inventory table with route, page name, Persona, and one-sentence responsibility

Do not output features, components, or state details.
```

## Round 4: Feature Slicing

Input: confirmed Round 3 output, processed page by page

Target artifact: Feature list and recommended vertical-slice structure

```text
Based on the confirmed Page Map below:

[Paste the Round 3 output]

## Current Task
Only perform Feature Slicing for these 1-3 pages:
[List one to three pages]

## Independence Signals
A capability should become a Feature when it meets at least 3:
- Independent business purpose
- Independent data source or state
- Independent interaction flow
- Likely to evolve independently
- Reusable across pages
- Testable independently

## Output Requirements
1. Feature list with feature name, responsibility, and state type: server, client, or both
2. Recommended vertical-slice directory structure
3. Which parts are `Shared Component` rather than Feature

Do not output Given-When-Then or implementation code.
```

## Round 5: Given-When-Then

Input: one confirmed Feature from Round 4

Target artifact: one `.feature` file in Gherkin

```text
Based on the confirmed Feature definition below:

Feature name: [feature name]
Responsibility: [one-line description]
Page: [page name]
Relevant Persona: [Persona]

## Task
Write a Given-When-Then acceptance spec in Gherkin format.

## Coverage Requirements
- Happy Path
- Edge Case
- Permission Case
- Error Case

## Writing Principles
- Be declarative and describe business intent
- Describe What, not UI click details

## Output Format
Output only the standard Gherkin .feature content.
```

## Round 6: Feature Spec And Delivery Planning

Input: approved artifacts from earlier rounds

Target artifact: Feature Spec set and implementation order recommendation

```text
Based on the completed analysis below:

## Persona
[Paste]

## Page Inventory
[Paste]

## Feature List
[Paste]

## Task
Plan the frontend implementation order using vertical-slice delivery.

## Prioritization Rules
1. Core user path first
2. Fewer dependencies first
3. Shared Component before dependent Features
4. Auth and permission Features early

## Output Requirements
1. Phase 1 / Phase 2 / Phase 3 plan
2. Which Features belong to each phase
3. What each phase can demonstrate
4. Feature dependencies
5. Which Feature should be implemented first and why
```

## Workflow Summary

| Round | Method Step | Input | Output | Granularity |
| --- | --- | --- | --- | --- |
| Round 1 | Persona | Project description | Persona cards | Whole project |
| Round 2 | Story Map | Round 1 | Story trees | Whole project |
| Round 3 | Page Map | Round 2 | Route tree and page inventory | Whole project |
| Round 4 | Feature Slicing | Round 3 | Feature list and directory structure | Per page batch |
| Round 5 | Given-When-Then | One Feature from Round 4 | Gherkin file | Per Feature |
| Round 6 | Feature Spec and planning | All approved artifacts | Specs and delivery order | Whole project |

The original methodology had 7 steps. `Component` and `State Boundary` are merged into Round 4 because they depend on Feature definitions and do not need a separate round.
