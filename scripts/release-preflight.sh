#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ $# -ne 0 ]; then
  echo "release-preflight.sh does not accept arguments" >&2
  exit 2
fi

echo "== Release preflight =="
echo "Running deterministic checks..."
.venv/bin/python -m pytest -q
.venv/bin/ruff check src/frontend_project_analysis tests
if rg -n "/Users/cherubines/Documents/MaxCPA" README.md SKILL.md references frontend-decomposition-methodology.md AGENTS.md --glob '!references/release-checklist.md'; then
  echo "Found stale absolute-path references above."
  exit 1
fi
git status --short

echo
echo "Manual parity audit:"
echo "- Compare changed code files with matching description files."
echo "- Compare changed description files with code paths, tests, and workflow rules."
echo "- Verify terminology against references/glossary.md."
echo "- Follow runbooks/release-doc-audit.md before tagging."
