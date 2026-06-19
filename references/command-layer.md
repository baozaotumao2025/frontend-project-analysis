# Command Layer

This page defines the repository's command hierarchy and which layer should be
considered canonical for each kind of operation.

## Layers

### 1. Skill layer

- The `frontend-project-analysis` skill should prefer `uv run fpa ...` for
  workflow operations.
- For repository maintenance and release actions, the skill should prefer the
  explicit shell scripts in `scripts/` when it needs to launch a local
  maintenance workflow.
- The skill should treat `make` as a grouped convenience wrapper, not as the
  canonical implementation layer.

### 2. Script layer

- `scripts/*.sh` are the canonical implementation entrypoints for repository
  maintenance, test, and release workflows.
- Scripts own the real orchestration logic, argument parsing, and process
  boundaries.
- If a workflow needs to be automated or called from the skill, prefer the
  script directly.

### 3. Make layer

- `Makefile` provides grouped, human-friendly aliases.
- Make targets should be organized by responsibility groups such as `test`,
  `quality`, and `release`.
- Primary grouped targets use dotted names such as `test.smoke`,
  `quality.lint`, and `release.card`; hyphenated names are retained only as
  compatibility aliases.
- A make target may wrap a script, but it should not become the only place where
  the workflow is documented or understood.

## Recommended Usage

- Use `make test`, `make quality`, and `make release` as the main entry points
  for humans.
- Use the more specific grouped targets when you need a single check, such as
  `make test.smoke`, `make quality.lint`, or `make release.card`.
- Use `scripts/*.sh` directly when you need the canonical automation behavior or
  want to call the workflow from the skill.

## Rules

- Do not add a new repository maintenance workflow only to `Makefile`; add the
  shell script first, then expose a grouped make target if human convenience
  needs it.
- If `Makefile` and `scripts/` disagree, treat the shell script as authoritative
  for execution behavior and update the make target to match.
- If `SKILL.md` and this page disagree, prefer this page for command-layer
  policy and update the skill text to match.
