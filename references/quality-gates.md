# Quality Gates

## Global Rules

- Output artifact first, then self-check, then pause
- Mark each checklist item with `OK`, `WARN`, or `FAIL`
- Do not pause with unresolved `FAIL`
- Do not skip rounds without explicit user approval
- Keep professional terms such as `Persona`, `Story Map`, `Feature Spec`, and `Happy Path` in English
- Every round must consume only `approved` and fresh upstream revisions; if an upstream revision is `stale`, the gate fails and the round must not advance

## Round 1

- [ ] Every recognizable user type has a Persona entry
- [ ] Every Persona file includes all required fields
- [ ] Permission boundaries are concrete
- [ ] `docs/personas/index.md` links all Persona files
- [ ] Separated Persona differ in real goals or paths

## Round 2

- [ ] Every Persona has its own Story Map
- [ ] Every Story Map has a clear start and end
- [ ] No page names or Feature names appear
- [ ] `docs/story-maps/index.md` links all Story Map files
- [ ] Activities describe real user goals rather than click sequences

## Round 3

- [ ] Every Story Step maps to a page or contextual surface
- [ ] Every page lists accessible Persona
- [ ] Page index and page files are consistent
- [ ] Persona-Story-Page matrix covers all main paths
- [ ] No orphan pages exist

## Round 4

- [ ] Every Feature in the current page batch has its own file
- [ ] Feature index and coverage matrix are updated
- [ ] `Shared Component` items are identified and not mislabeled as Features
- [ ] Each Feature meets at least 3 independence signals

The independence signals are:

- Independent business purpose
- Independent data or state
- Independent interaction flow
- Independent evolution potential
- Cross-page reuse potential
- Independent testability

## Round 5

- [ ] Includes `Happy Path`, `Permission Case`, `Error Case`, and `Edge Case`
- [ ] Every Scenario has complete `Given / When / Then`
- [ ] `Given` states the Persona clearly
- [ ] `When` remains declarative
- [ ] `Then` describes an observable business result

## Round 6

- [ ] Every Feature in `docs/features/` has a matching spec file
- [ ] Every spec includes the required fixed sections
- [ ] GWT content matches the approved `.feature` file
- [ ] `server state` and `client state` are clearly separated
