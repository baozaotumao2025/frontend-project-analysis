# ADR 0004: Host Review Fresh Context Isolation

## Status

Accepted

## Context

The workflow uses `host` mode when no external LLM provider is configured.

That keeps semantic review available, but it creates a risk if the same drafting context is reused for the review step:

- the reviewer may inherit the author's reasoning
- the review can become a self-justifying loop
- counterexamples may be suppressed by confirmation bias

We need a hard separation between the drafting context and the review context without requiring a different model.

Codex environments can spawn sub-agents, which gives us a practical way to create a fresh reviewer context inside the same overall task.

## Decision

Host semantic review MUST be executed in a fresh reviewer context that does not inherit the drafting conversation.

Specifically:

- The drafting context produces a frozen semantic packet.
- A fresh reviewer context reads only that packet.
- If the current Codex environment supports sub-agents, the reviewer context MUST be created with `spawn_agent` and `fork_context: false`.
- Same-session review is not an acceptable substitute when fresh sub-agent review is available.
- The reviewer output MUST include counterexamples and evidence-backed findings.
- If the output lacks either requirement, code MUST downgrade the decision to `needs_revision`.
- This same isolation rule also applies to packet-driven semantic review flows for the round chain and release review packet when host mode is used.

We keep the enforcement rules in `references/infrastructure.md`, `references/validation-matrix.md`, `references/cli-contract.md`, and `runbooks/host-review-isolation.md`.

## Alternatives Considered

### Reuse the drafting session and rely on prompt wording

Rejected because prompt wording alone does not isolate the reviewer from the author's reasoning.

### Require a different model instead of a different context

Rejected because the goal is review isolation, not model diversification.

### Leave host review informal and only document the preference

Rejected because the isolation requirement needs to be operationally hard, not advisory.

## Consequences

- Host review remains available without external API keys.
- Review quality becomes more defensible because the reviewer context is fresh.
- The workflow now depends on sub-agent support in Codex environments for the strongest host path.
- The review packet and result schema must remain strict enough to support evidence-based checks.

## Notes

- `runbooks/host-review-isolation.md` defines the operator procedure.
- `references/infrastructure.md` defines the runtime expectation for fresh reviewer contexts.
- `references/validation-matrix.md` defines the evidence and counterexample guard.
- `references/cli-contract.md` describes the user-visible impact of the guard.
