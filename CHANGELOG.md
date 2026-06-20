# Changelog

## [Unreleased]

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
