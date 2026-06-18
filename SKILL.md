---
name: frontend-project-analysis
description: Use when a user wants a document-first frontend project analysis workflow, including Persona definition, Story Map creation, Page Map mapping, Feature Slicing, Given-When-Then acceptance specs, or Feature Spec generation for a new or existing product.
---

# Frontend Project Analysis

Use this skill when the task is to analyze or decompose a frontend product into structured documentation artifacts rather than implementation code.

## When To Use

- The user wants to define `Persona`, `Story Map`, `Page Map`, `Feature`, `Given-When-Then`, or `Feature Spec`
- The user is starting a new project and wants a repeatable discovery workflow
- The user wants to break a large frontend scope into vertical slices and acceptance artifacts
- The expected output is Markdown or Gherkin documents
- The user wants Codex or Claude Code to perform semantic review directly from a generated packet when no external LLM is configured

Do not use this skill for component implementation, UI coding, or engineering execution unless the user explicitly pivots out of analysis.

## Read Order

Read these files before doing the workflow:

1. `references/methodology.md`
2. `references/glossary.md`
3. `references/structure.md`
4. `references/infrastructure.md`
5. `references/state-machine.md`
6. `references/workflow.md`
7. `references/quality-gates.md`

Only read `references/templates.md` when you need to create or expand output files.
If you need to check which document is authoritative for a topic, read `references/document-map.md`.

## Workflow Rules

- Follow the workflow round by round; do not skip rounds unless the user explicitly asks to do so
- If the user already has approved outputs from earlier rounds, resume from the latest approved round
- For each round, produce the artifact first, then a self-check against the matching quality gate, then pause
- Use `uv run fpa ...` commands to read or mutate workflow state instead of inferring graph consistency from Markdown alone
- If `FPA_LLM_PROVIDER=host`, do not call an external model from the skill; generate or inspect the packet and let the current Codex or Claude Code session make the semantic judgment
- Prefer small focused files and progressive disclosure over large catch-all documents
- Keep relationship-dense information in index or matrix files rather than inflating entity files
- Keep terminology aligned with `references/glossary.md`
- Keep artifact lifecycle semantics aligned with `references/state-machine.md`

## Output Conventions

- Default output roots are `docs/` and `specs/features/`
- Default document layout and file naming follow `references/structure.md`
- Use the templates in `references/templates.md` only as a starting point; adapt them to the project context
- Add structured frontmatter to workflow-managed Markdown artifact files so the CLI can validate type, round, status, and project alignment
- Professional terms such as `Persona`, `Story Map`, `Feature`, `Feature Spec`, `Happy Path`, `Edge Case`, `Permission Case`, and `Error Case` should remain in English

## Boundaries

- Put reusable workflow knowledge in this skill
- Put project-specific content in the target repository's documents
- Put repository-wide permanent behavior rules in that repository's `AGENTS.md`, not in this skill
