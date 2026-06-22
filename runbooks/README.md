# Runbooks

This directory collects maintenance procedures that are useful for repository operators but are not part of the `fpa` skill contract itself.

Runbooks describe how to execute a task. They should not define repository-wide policy, workflow semantics, or canonical terminology.

## Documents

| Document | Purpose |
| --- | --- |
| [`release-flow.md`](release-flow.md) | Preferred git release commit, tag, and push sequence |
| [`release-doc-audit.md`](release-doc-audit.md) | Release-time code/document/terminology parity audit |
| [`release-llm-review.md`](release-llm-review.md) | Fresh-session LLM review flow for frozen release packets |
| [`review-resubmit.md`](review-resubmit.md) | Operator steps for revalidating Markdown edits and stale revisions |
| [`test-matrix.md`](test-matrix.md) | Preferred test strategy for proving the skill works |
| [`coverage-baseline.md`](coverage-baseline.md) | Reproducible coverage baseline and guardrail notes |
| [`shortcut-manual.md`](shortcut-manual.md) | Natural-language goal and round-by-round command template |
| [`host-review-isolation.md`](host-review-isolation.md) | Operational steps for reviewing a frozen packet in a fresh host context |
| [`downstream-commit-flow.md`](downstream-commit-flow.md) | Step-by-step commit flow for generated downstream projects |
