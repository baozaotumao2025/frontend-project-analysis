# Release LLM Review

## Purpose

Use this runbook after the deterministic release preflight passes and you want a semantic review in a fresh-session reviewer context.

## Session Isolation Rule

- The LLM review must run in a fresh Codex or Claude Code session.
- Do not reuse the drafting session for the review.
- The reviewer session must read only the frozen packet produced by the script.
- If the reviewer context is not demonstrably fresh, the review is invalid.

## Flow

1. Run `./scripts/release-preflight.sh`.
2. If preflight fails, fix the problems and rerun it.
3. Run `./scripts/release-llm-review.sh`.
4. Open a fresh reviewer session and load only the generated packet.
5. Ask the reviewer to return JSON only, with counterexamples first and evidence-backed findings.
6. If the review reports issues, fix them in the drafting session and rerun the whole flow from step 1.
7. If the review is clean, proceed to commit and tag.

If you want the two phases wrapped into one maintainer-facing launcher, use `./scripts/release.sh`.
If you only want the compact reviewer card after preflight, use `./scripts/release-card.sh`.

## Review Criteria

- Code/document parity
- Terminology alignment with `references/glossary.md`
- Fresh-session isolation
- Release readiness

## Prompt Source

- The `brief assistant`, semantic review, and release review prompts live in [`src/frontend_project_analysis/core/prompts.py`](../src/frontend_project_analysis/core/prompts.py).
- The provider request builders that attach those prompts live in [`src/frontend_project_analysis/llm/structured.py`](../src/frontend_project_analysis/llm/structured.py), [`src/frontend_project_analysis/llm/payloads.py`](../src/frontend_project_analysis/llm/payloads.py), and [`src/frontend_project_analysis/llm/brief.py`](../src/frontend_project_analysis/llm/brief.py).
- The release review packet now carries a manifest, a reviewer card, a system prompt, and a user prompt, all rendered by [`scripts/release-llm-review.sh`](../scripts/release-llm-review.sh).
