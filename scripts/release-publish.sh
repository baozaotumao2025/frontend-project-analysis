#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

dry_run=0
remote=origin
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      dry_run=1
      shift
      ;;
    --remote)
      if [ $# -lt 2 ]; then
        echo "--remote requires a name" >&2
        exit 2
      fi
      remote="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
maintainer publish flow for the skill repository.
Usage: ./scripts/release-publish.sh [--dry-run] [--remote NAME]
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

version=$(.venv/bin/python - <<'PY'
from pathlib import Path

from frontend_project_analysis.release_policy import read_project_version

print(read_project_version(Path(".")))
PY
)

echo "== Maintainer release publish =="
echo "Target version: v${version}"

./scripts/release-preflight.sh
./scripts/test-full.sh
./scripts/test-e2e.sh
./scripts/release-llm-review.sh --skip-preflight

.venv/bin/python - <<'PY'
from pathlib import Path

from frontend_project_analysis.release_policy import assert_release_metadata

assert_release_metadata(Path("."))
PY

if [ "$dry_run" -eq 1 ]; then
  echo "Dry run enabled; skipping git commit, tag, and push."
  exit 0
fi

branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "HEAD" ]; then
  echo "release-publish.sh requires a checked-out branch" >&2
  exit 1
fi

git add CHANGELOG.md Makefile README.md SKILL.md pyproject.toml references runbooks scripts src tests agents/openai.yaml migrations
git commit -m "chore(release): v${version}"
if [ -n "$(git status --short)" ]; then
  echo "Working tree is still dirty after the release commit; resolve it before pushing." >&2
  git status --short
  exit 1
fi
git tag -a "v${version}" -m "v${version}"
git push "$remote" "$branch"
git push "$remote" "v${version}"
