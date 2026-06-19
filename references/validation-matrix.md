# Validation Matrix

## Purpose

This document separates validation into three responsibilities:

- `code`: deterministic structural and lifecycle enforcement
- `LLM` / host review: semantic judgment
- `projection`: derived indexes and matrices that should stay consistent with the source graph

The rule is simple: do not let the LLM decide whether a required field exists, whether a file is present, or whether a dependency is approved. Those are code-owned checks. Let the LLM judge meaning, coherence, and fit.

## Validation Layers

| Layer | Owner | Typical failure mode | Source of truth |
| --- | --- | --- | --- |
| Structural integrity | code | malformed file, missing section, missing reference, wrong frontmatter | workflow state + Markdown body |
| Lifecycle gate | code | upstream not approved, artifact stale, illegal transition | SQLite state + dependency graph |
| Semantic quality | LLM / host reviewer | weak reasoning, bad slicing, poor boundary, unclear wording, missing counterexamples or evidence | packet built from current revision |
| Derived projection | code | index or matrix drift | SQLite state + artifact bodies |

## Artifact Matrix

| Artifact | Code checks | LLM / host checks | Notes |
| --- | --- | --- | --- |
| `Persona` | frontmatter completeness; `artifact_type / slug / round / project` match DB; source exists; round gate freshness | role boundaries; core goal realism; permission boundary quality; invisible capability coverage | `analysis/personas/index.md` is a projection, not source of truth |
| `Story Map` | frontmatter completeness; `Start / End`; source exists; round gate freshness | activity validity; step ordering; no UI leakage; business coherence | `Activity -> Step -> Story` is a content contract, not a graph node contract |
| `Page` | frontmatter completeness; route / persona / responsibility / related feature references; source exists; round gate freshness | page boundary quality; surface coverage; shared-surface correctness | Matrices can report the lineage, but the page file owns the page scope |
| `Feature` | frontmatter completeness; page / persona / responsibility / state type / reuse / source story; source exists; round gate freshness | independence; coupling quality; slice clarity; delivery boundary honesty; evidence-backed findings and counterexamples | Feature is the main vertical-slice unit in the current workflow |
| `GWT` | scenario presence; complete `Given / When / Then`; required scenario names; source exists; round gate freshness | scenario intent; business-facing wording; behavioral coverage quality | The current code enforces scenario shape, not only syntax |
| `Feature Spec` | fixed section coverage; `server state` and `client state` both explicit; source exists; round gate freshness | boundary clarity; dependency honesty; cross-cutting completeness when relevant | This is where delivery-facing detail should become explicit |
| `brief assistant` | transcript capture; brief output file; optional AI follow-up and summary sections | follow-up question quality; synthesis quality; missing-gap detection | This is the LLM-assisted entry path for creating or refining a `project brief` |

## Host Review Guard

- `host` mode should be treated as a fresh review context, not a continuation of the drafting context.
- If Codex can spawn a sub-agent, that fresh context MUST be created with `fork_context: false`.
- Review prompts should force counterexamples first and require evidence-backed findings.
- If a semantic review output lacks counterexamples or concrete evidence, code should downgrade it to `needs_revision`.

## Structural Check Matrix

| Check | Enforced by | Implementation point | Result if failing |
| --- | --- | --- | --- |
| Frontmatter presence | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| Frontmatter identity match | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| Source file exists | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| Story Map `Start / End` | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| Page required sections | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| Feature required sections | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| GWT required scenarios and steps | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| Feature Spec required sections | code | `src/frontend_project_analysis/workflow/state/structural.py` | structural review fails |
| Hard dependency approved | code | `src/frontend_project_analysis/workflow/state/gates.py` | gate fails / approval blocked |
| Round freshness gate | code | `src/frontend_project_analysis/workflow/round_gates.py` | workflow start fails |
| Semantic review result | LLM / host | `src/frontend_project_analysis/core/prompts.py`, `src/frontend_project_analysis/commands/review/semantic_run.py` | semantic review passes, needs revision, or fails |

## Projection Matrix

These files are derived views and should be regenerated from the database and artifact bodies.

| Projection | Source data | Owner |
| --- | --- | --- |
| `analysis/index.md` | workflow workspace layout | code |
| `analysis/personas/index.md` | Persona bodies + metadata | code |
| `analysis/story-maps/index.md` | Story Map bodies + metadata | code |
| `analysis/pages/index.md` | Page bodies + metadata | code |
| `analysis/features/index.md` | Feature bodies + metadata | code |
| `analysis/relations/persona-story-page-matrix.md` | artifact graph lineage | code |
| `analysis/relations/feature-coverage-matrix.md` | artifact graph lineage | code |

## Practical Rule

If a question can be answered by parsing the file, checking the database, or traversing dependencies, it belongs in code.

If a question asks whether the artifact is convincing, coherent, or appropriately scoped, it belongs in semantic review.

If a question exists mainly so humans can browse lineage or coverage, it belongs in a projection.
