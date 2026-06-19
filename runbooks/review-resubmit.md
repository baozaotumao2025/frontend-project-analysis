# Review Resubmit

## Purpose

Use `fpa review resubmit` when a user has edited workflow-managed Markdown and wants to bring the target artifact back through structural and semantic review.

## Workflow

1. Run `fpa review resubmit --project <key> --artifact <ref>`.
2. If the environment is using a non-host provider, the command completes structural and semantic review in one pass.
3. If the environment is using `host`, the command writes a frozen semantic packet for a fresh reviewer context.
4. Use a fresh reviewer sub-agent with `fork_context: false` to review the packet.
5. Pass the resulting JSON back with `fpa review resubmit --project <key> --artifact <ref> --review-input <path>`.

## Notes

- The command accepts `draft`, `rejected`, `stale`, `structurally_valid`, `semantic_review`, and `approved` revisions when they need revalidation.
- If semantic review output lacks counterexamples or evidence, code downgrades it to `needs_revision`.
- If the user has edited Markdown but not yet re-imported it, the file tree and SQLite may be temporarily out of sync; `review resubmit` is the recommended one-step recovery path because it starts with a fresh import before any review decision is made.
