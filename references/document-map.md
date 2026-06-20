# Documentation Map

This page maps each concern to its canonical document.

## Scope Matrix

| Scope | Primary consumer | Included files |
| --- | --- | --- |
| `fpa` skill core | The `frontend-project-analysis` skill and its maintainers | `SKILL.md`, `references/methodology.md`, `references/workflow.md`, `references/quality-gates.md`, `references/infrastructure.md`, `references/state-machine.md`, `references/schema-sketch.md`, `references/validation-matrix.md`, `references/cli-contract.md`, `references/state-entrypoints.md`, `references/structure.md`, `references/templates.md`, `references/glossary.md`, `references/release-checklist.md`, `references/repo-layers.md`, `references/command-layer.md`, `references/adr/*.md` |
| Generated project submission guidance | Users of `fpa` output in downstream repositories | `references/downstream-commit-policy.md`, `runbooks/downstream-commit-flow.md` |
| Repository governance | All agents operating in this repository | `AGENTS.md` |
| Operator runbooks | Repository operators and maintainers | `runbooks/README.md`, `runbooks/*.md`, `scripts/README.md` |
| User-facing summary | Human readers | `README.md` |
| Skill launcher config | Codex, marketplace, or agent launcher | `agents/openai.yaml` |
| Working note | Humans, with non-authoritative status | `frontend-decomposition-methodology.md` |

## Placement Guide

| If the content is about... | Put it in... |
| --- | --- |
| workflow rounds, gates, artifact semantics, or canonical analysis rules | `references/*` |
| repository-wide permanent behavior rules for agents | `AGENTS.md` |
| step-by-step execution, maintenance, release, or test procedures | `runbooks/*` |
| default output layout, naming rules, or file responsibility boundaries for `fpa` | `references/structure.md` |
| downstream submission policy for generated projects | `references/downstream-commit-policy.md` |
| project overview, install notes, and human-readable maintenance summary | `README.md` |
| launcher metadata for the skill package | `agents/openai.yaml` |
| maintainer command wrappers and short shell notes | `scripts/README.md` |
| non-authoritative scratch or transition notes | working note files such as `frontend-decomposition-methodology.md` |

| Document | Layer | Purpose | Authority |
| --- | --- | --- | --- |
| `README.md` | Summary | Project overview, capabilities, usage, and maintenance | User-facing summary |
| `SKILL.md` | Summary | Skill entrypoint and reading order | Operational entrypoint |
| `AGENTS.md` | Policy | Repository-wide permanent behavior rules | Repository governance |
| `references/methodology.md` | Reference | 6-round analysis workflow | Canonical workflow source |
| `references/workflow.md` | Reference | Round-by-round inputs and outputs | Canonical workflow shape |
| `references/quality-gates.md` | Reference | Per-round quality gates | Canonical review checklist |
| `references/infrastructure.md` | Reference | Runtime architecture and storage model | Canonical backend behavior |
| `references/state-machine.md` | Reference | Artifact lifecycle semantics | Canonical status semantics |
| `references/schema-sketch.md` | Reference | Node, edge, and matrix placement for the workflow schema | Canonical schema sketch |
| `references/validation-matrix.md` | Reference | Code, LLM, and projection validation responsibilities | Canonical validation matrix |
| `references/cli-contract.md` | Reference | CLI behavior under code-enforced gates | Canonical user-facing command contract |
| `references/state-entrypoints.md` | Reference | Which commands can mutate workflow state | Canonical entrypoint map |
| `references/structure.md` | Reference | Output layout, naming rules, and responsibility boundaries | Canonical file layout guide |
| `references/templates.md` | Reference | Managed file templates and required section shapes | Canonical file shape guide |
| `references/adr/index.md` | ADR | Architectural decision records | Canonical design rationale |
| `references/adr/relationship-map.md` | ADR | Relationship matrix for decision boundaries | ADR overlap check |
| `references/repo-layers.md` | Reference | Repository layout and reading order | Structural navigation guide |
| `references/release-checklist.md` | Reference | Public release boundary and preflight checks | Release preparation guide |
| `references/command-layer.md` | Reference | Command hierarchy and canonical execution layer | Command-layer policy |
| `references/glossary.md` | Reference | Terms and naming rules | Canonical vocabulary |
| `references/downstream-commit-policy.md` | Reference | Commit, type, version, and push policy for generated projects | Downstream submission policy |
| `runbooks/README.md` | Runbook index | Operational procedures and maintenance workflows | Operator-facing procedure index |
| `runbooks/*.md` | Runbook | Step-by-step maintenance and release procedures | Executable procedures |
| `runbooks/downstream-commit-flow.md` | Runbook | Step-by-step submission flow for generated projects | Downstream contributor procedure |
| `frontend-decomposition-methodology.md` | Working note | Lightweight working note and index | Non-authoritative index only |

## Rules

- If `README.md` and a `references/*` file disagree, prefer the `references/*` file.
- If `SKILL.md` and `references/methodology.md` disagree, prefer `references/methodology.md`.
- If `AGENTS.md` and a lower-layer document disagree on repository-wide governance, prefer `AGENTS.md` and update the lower-layer document to match.
- If a concern is about execution steps rather than stable meaning, prefer `runbooks/*` over `references/*`.
- If `frontend-decomposition-methodology.md` disagrees with anything else, treat it as stale until updated.
- If you are checking vocabulary for `project brief`, `brief interview`, `brief assistant`, `transcript`, or `preflight helper`, prefer `references/glossary.md`
- If you are checking which commands prepare input without mutating workflow state, prefer `references/state-entrypoints.md` and `references/workflow.md`
