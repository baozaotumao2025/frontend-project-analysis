# Schema Sketch

## Purpose

This document compresses the current workflow model into a concrete schema sketch.
It separates four concerns:

- `node`: durable artifact identity and revision ownership
- `edge`: explicit relationships between nodes
- `index/matrix`: derived projections for browsing and reporting
- `evidence control`: round-local inventory and coverage state used to freeze review inputs

The rule of thumb is simple: if something needs its own approval, stale propagation, or rollback lineage, it belongs on a node. If it only expresses a relationship, it belongs on an edge. If it is primarily a view for humans, it belongs in an index or matrix. If it is only needed to decide whether a round has fully enumerated and reconciled its evidence, it belongs in the evidence control layer rather than becoming a durable graph node.

## Node Layer

### Core tables

| Table | Purpose | Fields that belong here | Fields that should not live here |
| --- | --- | --- | --- |
| `projects` | Project container | `key`, `name`, `root_path`, timestamps | Artifact content, dependency links |
| `artifacts` | Stable artifact identity plus current lifecycle state | `project_id`, `artifact_type`, `slug`, `title`, `round`, `status`, `source_path`, `current_version_id`, timestamps | Story steps, scenarios, page mappings, coverage rows |
| `artifact_versions` | Revision snapshot for one artifact | `artifact_id`, `version_no`, `content_hash`, `metadata_json`, `body_snapshot`, `created_by`, `created_at` | Cross-artifact edges, approval state, derived indexes |

### How to read the node layer

- `artifacts` is the node envelope.
- `artifact_versions` is the revision payload.
- `status` lives on the node envelope because approval, freshness, stale propagation, and supersession are revision-aware lifecycle concerns.
- `metadata_json` is acceptable for parser output or light structured hints, but not for replacing explicit edges or index rows.
- `analysis_inventory`, `coverage ledger`, and `frozen packet` details are round-local control data; they should be represented as ephemeral workflow state or packet content, not as durable graph nodes unless a future ADR explicitly promotes them.

### Content placement by artifact type

| Artifact type | Put in the revision body | Put in node metadata only if needed | Do not model as separate nodes unless independently governed |
| --- | --- | --- | --- |
| `Persona` | role, core goal, key difference, permission boundary, invisible pages/capabilities | parser hints, source provenance | persona sub-phrases |
| `Story Map` | `Activity -> Step -> Story` text | start/end markers if needed for rendering | individual steps as stateful nodes |
| `Page` | route scope, accessible Persona, page responsibility, Story Step coverage | route alias, page category | route fragments, micro-interactions |
| `Feature` | feature responsibility, page, Persona served, state type, reuse notes, source story | implementation hints | sentence-level acceptance fragments |
| `GWT` | scenarios and Given/When/Then blocks | scenario labels, grouping hints | individual scenario clauses |
| `Feature Spec` | implementation boundary, dependency notes, delivery constraints, cross-cutting concerns | release flags, environment notes | paragraph-level subclaims |

## Edge Layer

### Relationship table

| Table | Purpose | Fields that belong here | Fields that should not live here |
| --- | --- | --- | --- |
| `artifact_dependencies` | Directed relationship between two artifact nodes | `from_artifact_id`, `to_artifact_id`, `dependency_type`, `is_hard`, `created_at` | status, review result, narrative justification |

### Edge semantics

Use edges for relationship verbs, not for lifecycle meaning.

- `requires`: hard upstream prerequisite
- `derived_from`: revision or analysis lineage
- `covers`: coverage relation between analysis layers
- `serves`: who the artifact serves
- `implements`: implementation mapping
- `supersedes`: explicit replacement lineage when one node replaces another

Do not create a separate node just to say "this changed". That belongs in `artifact_versions` plus `artifact_transitions`.

### Event and audit sidecars

These are not graph edges, but they preserve the history of graph changes.

| Table | Purpose | Fields that belong here |
| --- | --- | --- |
| `artifact_transitions` | append-only lifecycle history | `artifact_id`, `from_status`, `to_status`, `reason`, `actor`, `created_at` |
| `artifact_reviews` | structural or semantic review record | `artifact_id`, `version_id`, `review_kind`, `review_status`, `reviewer_kind`, `summary`, `reviewer_ref`, `payload_json`, `created_at` |
| `artifact_review_findings` | review findings | `review_id`, `severity`, `code`, `message`, `details_json` |
| `provider_call_audits` | provider request/response audit trail | `artifact_id`, `review_id`, `provider_name`, `trace_id`, `request_id`, `model_name`, `endpoint`, `call_status`, `attempt_count`, `duration_ms`, `request_path`, `response_path`, summaries, `error_message`, `created_at` |

## Index And Matrix Layer

These files are projections, not source of truth. They should be regenerated from the database and the artifact bodies.

| File | Purpose | Typical columns |
| --- | --- | --- |
| `analysis/personas/index.md` | Persona browsing | Persona, Core Goal, Story Map, Notes |
| `analysis/story-maps/index.md` | Story Map browsing | Persona, Story Map, Start, End |
| `analysis/pages/index.md` | Page inventory | Route, Page Name, Accessible Persona, Responsibility |
| `analysis/features/index.md` | Feature inventory | Feature, Responsibility, Page, Persona Served, State Type, Cross-Page Reuse |
| `analysis/relations/persona-story-page-matrix.md` | lineage matrix | Persona, Story Map, Page, Feature |
| `analysis/relations/feature-coverage-matrix.md` | feature coverage matrix | Feature, Service Persona, Source Page, Covered Story |
| round-local inventory / coverage view | evidence control projection | File, Disposition, Reason, Frozen Packet Reference |

### What belongs in a matrix instead of a node

- Persona to Story to Page lineage
- Feature to Story coverage
- Shared surface membership
- Cross-page reuse reporting
- "Which artifact touches which user path" lookups

If a field exists mainly so a report can answer a browsing question, keep it in a matrix or index.

## Practical Placement Rules

1. Put stable identity and current lifecycle state on `artifacts`.
2. Put revision content and parser output on `artifact_versions`.
3. Put relationship verbs on `artifact_dependencies`.
4. Put lifecycle history on `artifact_transitions`.
5. Put review evidence on `artifact_reviews` and `artifact_review_findings`.
6. Keep `analysis_inventory`, `coverage ledger`, and `frozen packet` data out of the durable graph unless the workflow later needs their own lifecycle.
7. Put human-facing summaries and lookup tables in `analysis/*/index.md` and `analysis/relations/*.md`.

## Bottom Line

The current model is already shaped correctly:

- node = revisioned artifact identity
- edge = dependency and lineage
- matrix = browsable derived view

The main optimization left is to keep sub-steps, scenario fragments, and durable coverage rows out of the graph unless they truly need their own lifecycle.
