# Documentation Map

This page maps each concern to its canonical document.

| Document | Layer | Purpose | Authority |
| --- | --- | --- | --- |
| `README.md` | Summary | Project overview, capabilities, usage, and maintenance | User-facing summary |
| `SKILL.md` | Summary | Skill entrypoint and reading order | Operational entrypoint |
| `references/methodology.md` | Reference | 6-round analysis workflow | Canonical workflow source |
| `references/workflow.md` | Reference | Round-by-round inputs and outputs | Canonical workflow shape |
| `references/quality-gates.md` | Reference | Per-round quality gates | Canonical review checklist |
| `references/infrastructure.md` | Reference | Runtime architecture and storage model | Canonical backend behavior |
| `references/state-machine.md` | Reference | Artifact lifecycle semantics | Canonical status semantics |
| `references/schema-sketch.md` | Reference | Node, edge, and matrix placement for the workflow schema | Canonical schema sketch |
| `references/validation-matrix.md` | Reference | Code, LLM, and projection validation responsibilities | Canonical validation matrix |
| `references/test-matrix.md` | Reference | Test strategy and coverage plan for proving the skill works | Canonical test matrix |
| `references/cli-contract.md` | Reference | CLI behavior under code-enforced gates | Canonical user-facing command contract |
| `references/state-entrypoints.md` | Reference | Which commands can mutate workflow state | Canonical entrypoint map |
| `references/structure.md` | Reference | Output layout, naming rules, and responsibility boundaries | Canonical file layout guide |
| `references/templates.md` | Reference | Managed file templates and required section shapes | Canonical file shape guide |
| `references/adr/index.md` | ADR | Architectural decision records | Canonical design rationale |
| `references/repo-layers.md` | Reference | Repository layout and reading order | Structural navigation guide |
| `references/release-checklist.md` | Reference | Public release boundary and preflight checks | Release preparation guide |
| `references/glossary.md` | Reference | Terms and naming rules | Canonical vocabulary |
| `frontend-decomposition-methodology.md` | Working note | Lightweight working note and index | Non-authoritative index only |

## Rules

- If `README.md` and a `references/*` file disagree, prefer the `references/*` file.
- If `SKILL.md` and `references/methodology.md` disagree, prefer `references/methodology.md`.
- If `frontend-decomposition-methodology.md` disagrees with anything else, treat it as stale until updated.
- If you are checking vocabulary for `project brief`, `brief interview`, `transcript`, or `preflight helper`, prefer `references/glossary.md`
- If you are checking which commands prepare input without mutating workflow state, prefer `references/state-entrypoints.md` and `references/workflow.md`
