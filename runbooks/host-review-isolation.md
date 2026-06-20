# Host Review Isolation

## Purpose

Use this workflow when semantic review must run in `host` mode but should not reuse the drafting conversation.

The goal is not to force a different model. The goal is to force a different reviewer context with only the frozen packet as input.

## Required Separation

- The drafting session produces the artifact and the packet.
- A fresh reviewer session reads only the packet.
- The reviewer session must not inspect the drafting chat, hidden scratch work, or intermediate reasoning.
- The reviewer session must return JSON only.
- The reviewer result must include counterexamples and evidence-backed findings.
- This separation applies to semantic review for the round chain, `review resubmit`, and the release packet flow.

## Practical Steps

1. Run `fpa review semantic-packet --project <key> --artifact <ref> --output <path>` or `fpa review semantic-run --project <key> --artifact <ref> --output <path>`.
2. If the current Codex environment supports sub-agents, spawn a fresh reviewer sub-agent with `fork_context: false`.
3. Otherwise open a new Codex or Claude Code session that has not participated in drafting the artifact.
4. Load only the packet file into that fresh reviewer context.
5. Ask the reviewer to list counterexamples first, then return a JSON semantic review result.
6. Reject any review result that lacks `counterexamples` or any `finding.evidence`.
7. Record the JSON with `fpa review semantic-record --project <key> --artifact <ref> --input <path>`.

## Operator Rule

- If the reviewer context is not demonstrably fresh, treat the review as invalid.
- If the review output is missing evidence or counterexamples, code will downgrade it to `needs_revision`.
