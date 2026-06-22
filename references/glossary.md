# Glossary

## Usage Rules

- Prefer the terms defined in this file
- Terms marked as English-only should remain in English in artifacts, templates, and self-checks
- If you add a new domain term, add it here before using it elsewhere

## English-Only Core Terms

- `Persona`
- `Story Map`
- `Page Map`
- `Feature`
- `Feature Slicing`
- `Given-When-Then`
- `Feature Spec`
- `Happy Path`
- `Edge Case`
- `Permission Case`
- `Error Case`
- `Given`
- `When`
- `Then`
- `server state`
- `client state`
- `Shared Component`
- `analysis_inventory`
- `coverage ledger`
- `frozen packet`
- `independent worker`
- `revision`
- `fresh`
- `fresh-session`
- `stale`
- `superseded`
- `archived`
- `gate`

## Preferred Wording

- Write `Persona definition`, not a translated substitute
- Write `Story Map`, not a translated substitute
- Write `Page Map`, not a translated substitute
- Write `Feature Slicing`, not a translated substitute
- Write `Given-When-Then`, not a translated substitute
- Write `Feature Spec` as the primary heading
- Write `Happy Path`, `Edge Case`, `Permission Case`, and `Error Case` in English
- Write `Given / When / Then` in English
- Write `Shared Component` as the primary term
- Write `revision` for a versioned artifact instance
- Write `fresh` for an approved revision that is not invalidated by upstream change
- Write `fresh-session` for a reviewer context that must not reuse the drafting conversation
- Write `stale` for a revision that must be revalidated because upstream changed
- Write `superseded` for a revision replaced by a newer approved revision
- Write `archived` for a retained revision that is no longer part of active workflow
- Write `server state` for persisted workflow or backend-owned state
- Write `client state` for local UI-owned state or transient presentation state
- Write `analysis_inventory` for the explicit evidence set a round is allowed to inspect
- Write `coverage ledger` for the per-file disposition table in a round
- Write `frozen packet` for a review snapshot that must not drift with the drafting context
- Write `independent worker` for a reviewer context that must not reuse the drafting context

## Input Preparation Terms

- Write `project brief` for the user-owned input that describes the product, users, scenarios, and constraints before `init`
- Write `draft brief` for a brief that has been collected but not yet confirmed
- Write `confirmed brief` for a brief that has been explicitly confirmed and carries provenance metadata
- Write `brief interview` for the bounded Q&A flow that helps a user collect or refine a `project brief`
- Write `brief assistant` for the LLM-assisted helper that suggests follow-up questions and synthesizes a project brief
- Write `brief confirm` for the confirmation step that turns a draft brief into a confirmed brief
- Write `transcript` for the saved question-and-answer record produced by `brief interview`
- Write `preflight helper` for commands that prepare input without mutating workflow state

## Cross-Cutting Terms

- Write `discovery` for the evidence-gathering phase that separates confirmed facts from assumptions
- Write `evidence` for the source material behind a project brief or downstream analysis decision
- Write `risk` for a known uncertainty that could break the plan, quality, or delivery path
- Write `assumption` for a statement that is currently unverified but being used for planning
- Write `accessibility` for keyboard, screen reader, semantic, and contrast requirements
- Write `observability` for logs, metrics, traces, and signals used to understand behavior in production
- Write `release` for rollout, rollout guardrails, rollback, and deployment readiness concerns
- Write `compliance` for privacy, legal, regulatory, or policy constraints

## Downstream Submission Terms

- Write `generated project` for a repository created from `fpa` analysis output
- Write `downstream project` for the user-owned repository that receives generated artifacts
- Write `submission bundle` for the coherent set of files that should be committed together
- Write `commit type` for the custom generated-project classification used in commit messages
- Write `analysis` for changes to generated analysis artifacts such as Personas, Story Maps, Page Maps, Features, GWT, and Feature Specs
- Write `sync` for changes that align generated docs, README, changelog, or other project surfaces
- Write `release` for changes to version metadata, changelog release sections, tags, or release notes
- Write `policy` for changes to the rules that govern generated-project structure or workflow
- Write `tooling` for changes to scripts, automation, validation, or supporting command surfaces
- Write `maintainer publish` for the skill repository's own release flow
- Write `downstream submit` for the user-owned generated-project submission flow
- Write `natural language routing` for the user-facing classification step that chooses between `maintainer publish` and `downstream submit`

## Workflow Modes

- Write `Formal mode` for the entry path that consumes only `approved` and `fresh` upstream revisions and produces canonical workflow artifacts
- Write `Explore mode` for the entry path that may read draft or unapproved upstream material for local analysis, without advancing canonical lifecycle state
