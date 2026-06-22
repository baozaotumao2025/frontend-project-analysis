# Validation Matrix

## Purpose

This document separates validation into three responsibilities:

- `code`: deterministic structural and lifecycle enforcement
- `LLM` / host review: semantic judgment in a fresh reviewer context
- `projection`: derived indexes and matrices that should stay consistent with the source graph
- `evidence control`: inventory, coverage, and frozen packet reconciliation before review

The rule is simple: do not let the LLM decide whether a required field exists, whether a file is present, or whether a dependency is approved. Those are code-owned checks. Let the LLM judge meaning, coherence, and fit.

## Validation Layers

| Layer | Owner | Typical failure mode | Source of truth |
| --- | --- | --- | --- |
| Structural integrity | code | malformed file, missing section, missing reference, wrong frontmatter | workflow state + Markdown body |
| Lifecycle gate | code | upstream not approved, artifact stale, illegal transition | SQLite state + dependency graph |
| Semantic quality | LLM / host reviewer | weak reasoning, bad slicing, poor boundary, unclear wording, missing counterexamples or evidence | packet built from current revision; host mode must use a fresh reviewer sub-agent when available |
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

## Evidence Control Matrix

| Control surface | Code checks | Semantic checks | Notes |
| --- | --- | --- | --- |
| `analysis_inventory` | file enumeration, scope boundaries, missing item detection | evidence completeness, scope honesty | This is the first checkpoint before abstraction |
| `coverage ledger` | every item has `mapped`, `excluded`, or `needs_review` | exclusion rationale quality, unresolved ambiguity | No round should proceed with blank coverage |
| `frozen packet` | packet is snapshot-based and immutable for the review step | reviewer only sees the frozen packet | Prevents context drift |
| `independent worker` | fresh context isolation | counterexample-first review quality | Required when host mode is used |

## LLM Validation Matrix

| Validation entry | What it checks | Fresh-context rule | Notes |
| --- | --- | --- | --- |
| `brief assistant` | Guided follow-up and synthesis for a project brief | Any downstream host review of the generated packet must use a fresh reviewer sub-agent context | This is the only LLM-assisted brief-convergence path |
| Round 1 semantic review | Persona boundaries, goals, and cross-cutting signals | If host review is used, the packet must be judged in a fresh reviewer sub-agent context | Structural checks remain code-owned |
| Round 2 semantic review | Story Map coherence and story ordering | If host review is used, the packet must be judged in a fresh reviewer sub-agent context | Reviewer should only see the frozen packet |
| Round 3 semantic review | Page responsibility and surface coverage | If host review is used, the packet must be judged in a fresh reviewer sub-agent context | Same packet-only rule as other rounds |
| Round 4 semantic review | Feature slicing, coupling, and state type clarity | If host review is used, the packet must be judged in a fresh reviewer sub-agent context | Feature review is where delivery slicing tightens |
| Round 5 semantic review | GWT intent, evidence, and behavior wording | If host review is used, the packet must be judged in a fresh reviewer sub-agent context | `Given / When / Then` must stay business-facing |
| Round 6 semantic review | Feature Spec completeness and delivery planning | If host review is used, the packet must be judged in a fresh reviewer sub-agent context | Accessibility, observability, release, and compliance must remain visible when relevant |
| `review resubmit` host handoff | Reconciled Markdown plus fresh packet export | Must export a frozen packet for a fresh reviewer context | Canonical recovery path after manual Markdown edits |
| Release packet review | Release parity, terminology, and readiness | Must be reviewed in a fresh reviewer session or sub-agent context | Uses the release packet/card wrapper rather than drafting context |

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

Derived projections may also include round-local inventory and coverage views when those help humans inspect whether the evidence boundary was fully reconciled.

## Practical Rule

If a question can be answered by parsing the file, checking the database, or traversing dependencies, it belongs in code.

If a question asks whether the artifact is convincing, coherent, or appropriately scoped, it belongs in semantic review.

If a question exists mainly so humans can browse lineage or coverage, it belongs in a projection.
