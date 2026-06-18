# ADR Index

This directory records architectural and workflow decisions that are important enough to keep as durable rationale.

## Records

| ADR | Title | Status | Purpose |
| --- | --- | --- | --- |
| `0001-revision-aware-state-gates.md` | Revision-Aware State Gates And Recovery | Accepted | Defines the revision-aware gate model and rollback semantics |
| `0002-document-layering-and-rule-placement.md` | Document Layering And Rule Placement | Accepted | Defines where summaries, rules, and rationale belong |

## Reading Guide

- Read the ADR when you need the rationale behind a canonical reference rule.
- Read `references/state-machine.md` for lifecycle semantics.
- Read `references/workflow.md` for round-by-round gates and recovery behavior.
- Read `references/quality-gates.md` for checklist-level enforcement.
