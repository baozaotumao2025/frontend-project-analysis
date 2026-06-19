#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

output=""
while [ $# -gt 0 ]; do
  case "$1" in
    --output)
      if [ $# -lt 2 ]; then
        echo "--output requires a path" >&2
        exit 2
      fi
      output="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./scripts/release.sh [--output PATH]
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

./scripts/release-preflight.sh

if [ -n "$output" ]; then
  ./scripts/release-llm-review.sh --skip-preflight --output "$output"
else
  ./scripts/release-llm-review.sh --skip-preflight
fi
