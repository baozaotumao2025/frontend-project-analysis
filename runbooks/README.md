# Runbooks

This directory collects maintenance procedures that are useful for repository operators but are not part of the `fpa` skill contract itself.

Runbooks describe how to execute a task. They should not define repository-wide policy, workflow semantics, or canonical terminology.

## Documents

| Document | Purpose |
| --- | --- |
| [`release-flow.md`](release-flow.md) | Preferred git release commit, tag, and push sequence |
| [`release-doc-audit.md`](release-doc-audit.md) | Release-time code/document/terminology parity audit |
| [`release-llm-review.md`](release-llm-review.md) | Fresh-session LLM review flow for release packets |
| [`review-resubmit.md`](review-resubmit.md) | Operator steps for revalidating Markdown edits and stale revisions |
| [`test-matrix.md`](test-matrix.md) | Preferred test strategy for proving the skill works |
| [`host-review-isolation.md`](host-review-isolation.md) | Operational steps for reviewing a frozen packet in a fresh host context |
