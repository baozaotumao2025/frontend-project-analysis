# Changelog

## [Unreleased]

## [1.4.0] - 2026-06-25

### Added

- Unified relation-row projection across the three matrix views so `Persona`, `Story Map`, `Page`, `Feature`, and `GWT` coverage now stays consistent across every exported relation surface.
- Clickable relation matrices plus `analysis/relations/index.md` and `analysis/relations/graph.html` as first-class browsing surfaces for relationship-heavy analysis output.
- `export graph-json` for machine-readable relationship graph export with canonical `rows`, `nodes`, `edges`, stable `group` / `layout` metadata, and precomputed adjacency and traversal fields such as `adjacent_refs`, `upstream_refs`, and `downstream_refs`.
- `export graph-html` for a static interactive relationship graph that supports deep links, focus filters, path-scope controls, and URL-restorable view state.

### Changed

- GWT artifacts now require an explicit frontmatter `feature` binding and relation export validates that the frontmatter binding and hard dependency graph stay aligned.
- Relation matrices now include full five-column coverage (`Persona | Story Map | Page | Feature | GWT`, reordered per view) instead of partial projections.
- Relationship exports now share one canonical graph builder so Markdown matrices, graph JSON, and graph HTML no longer drift from each other.
- Matrix deep links now open the relationship graph with type-aware default path direction: `Persona` opens downstream, `GWT` opens upstream, and `Feature` opens both directions.

### Fixed

- Relation exports now fail closed when a `GWT` references a missing `Feature`, when graph bindings disagree with hard dependencies, or when matrix coverage would otherwise miss or hallucinate artifacts.
- HTML graph state is now shareable and reproducible because focus, filter, and path-scope changes are synchronized back into the URL.

### Notes

- Release doc parity for the relationship export surfaces was tightened so the template inventory now includes `analysis/features/index.md` and `analysis/relations/graph.html`.
- Release-facing infrastructure docs now state explicitly that `import markdown-scan --apply` refreshes indexes and relation matrices, but does not regenerate `graph.html` or `*-graph.json` exports.

## [1.3.4] - 2026-06-20

### Added

- Natural-language submission routing with the `fpa submit` entrypoint for maintainer publish and downstream submit flows.
- Configurable prompt templates for submission intent routing so the router follows the same override pattern as other LLM-assisted flows.
- A downstream project commit policy for generated analysis bundles, including bundle shape, version syncing, changelog, push, and tag rules.
- An ADR relationship map to help maintainers check for decision overlap before adding new governance records.

### Changed

- README navigation now surfaces the natural-language submission route alongside the existing workflow commands.
- The CLI now exposes `submit` as a first-class command and routes ambiguous requests conservatively.
- The maintainer release bundle now includes version metadata, changelog, ADR guidance, and routing documentation updates.

### Fixed

- Ambiguous natural-language submission requests now fail closed instead of leaking into the wrong workflow.
- Submission routing no longer conflates maintainer publish with downstream project submission.

## [1.3.3] - 2026-06-20

### Added

- Maintainer-only `release.publish` / `release-publish` flow that runs preflight, regression, release review, version checks, commit, tag, and push in one action.
- Release metadata validation for `pyproject.toml`, `src/frontend_project_analysis/__init__.py`, and `CHANGELOG.md`.

### Changed

- Release docs now separate the packet-generation chain from the maintainer publish chain.

## [1.3.2] - 2026-06-20

### Added

- ADR 0007 now records the locale-tolerant cross-reference rule for Page and Feature authoring.

### Changed

- Fresh-context guidance now applies to all packet-driven LLM validation flows, including brief-assisted convergence, round-chain semantic review, review resubmit, and release review.
- Structural validation now accepts canonical labels, frontmatter aliases, and resolvable Markdown links in cross-reference sections, which makes localized authoring less brittle.
- `analysis/pages/[page-slug].md` and `analysis/features/[feature-name].md` template guidance now documents the accepted cross-reference forms.

### Fixed

- Localized labels such as Chinese Persona names no longer need to match a bare English title exactly when a canonical alias or resolvable Markdown link is available.
- Markdown link style cross-references now resolve through the structural validator instead of being treated as unknown text.

## [1.3.1] - 2026-06-20

### Added

- Draft brief confirmation flow: `brief interview` and `brief assistant` now produce draft briefs, `brief confirm` promotes them to confirmed briefs, and `init` requires confirmed provenance before bootstrapping.
- Explicit release guidance for confirmed briefs so initialization no longer accepts bare markdown as an implied source of truth.
- Clarified launcher-agnostic usage for both Codex and Claude Code, including the host-review packet flow.

### Changed

- `init` now rejects unconfirmed brief input instead of silently treating it as authoritative.
- The regression suite now covers draft briefs, confirmation, and confirmed bootstrap behavior end to end.

## [1.3.0] - 2026-06-19

### Added

- `workflow explore` as a discoverable exploratory entrypoint alongside the canonical formal workflow.
- `Formal mode` / `Explore mode` terminology and release guidance for the split between canonical delivery and exploratory analysis.
- Release readiness criteria that require `workflow explore start` to succeed without mutating canonical lifecycle state.
- `fpa review resubmit` as a one-step recovery command for manual Markdown edits and stale revisions.
- Host review isolation guidance that requires a fresh reviewer sub-agent with `fork_context: false` when Codex sub-agents are available.
- Review guards that require counterexamples and evidence-backed findings for semantic review acceptance.

### Changed

- `workflow start` remains the formal hard gate, while `workflow explore start` allows later-round analysis against draft or unapproved upstream material.
- Release-facing workflow docs now describe both formal and exploratory entrypoints.
- The release checklist now explicitly states how to judge readiness for the new workflow split.
- Markdown edits are now explicitly treated as a transiently divergent input until `import markdown-scan --apply` or `review resubmit` reconciles them into SQLite.
- Host semantic review now exports a frozen packet for a fresh reviewer context instead of relying on same-session review.

### Notes

- The formal chain still requires approved and fresh upstream revisions.
- Explore mode is intentionally non-canonical and does not replace the approval flow.
- This repository keeps SQLite as the authoritative workflow state store.
- `analysis/` remains the human-editable projection layer.
