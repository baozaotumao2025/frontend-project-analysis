# ADR Index

This directory records durable architectural and workflow decisions.

## Records

| ADR | Title | Status | Purpose |
| --- | --- | --- | --- |
| `0001-revision-aware-state-gates.md` | Revision-Aware State Gates And Recovery | Accepted | Defines the revision-aware gate model and rollback semantics |
| `0002-document-layering-and-rule-placement.md` | Document Layering And Rule Placement | Accepted | Defines where summaries, rules, and rationale belong |
| `0003-cross-cutting-analysis-and-brief-convergence.md` | Cross-Cutting Analysis And Brief Convergence | Accepted | Defines how the brief interview and cross-cutting concerns flow through the workflow |
| `0004-host-review-fresh-context-isolation.md` | Host Review Fresh Context Isolation | Accepted | Requires host semantic review to use a fresh reviewer context |
| `0005-review-resubmit-and-import-first-reconciliation.md` | Review Resubmit And Import-First Reconciliation | Accepted | Defines the recovery path for manual Markdown edits and stale revisions |
| `0006-formal-and-explore-workflow-modes.md` | Formal And Explore Workflow Modes | Accepted | Defines the split between canonical delivery and exploratory analysis |

## Reading Guide

- Read the ADR when you need the rationale behind a canonical reference rule.
- Read `references/state-machine.md` for lifecycle semantics.
- Read `references/workflow.md` for round-by-round gates and recovery behavior.
- Read `references/quality-gates.md` for checklist-level enforcement.
