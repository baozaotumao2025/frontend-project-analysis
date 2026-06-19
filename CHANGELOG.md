# Changelog

## [Unreleased]

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
