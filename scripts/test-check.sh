#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m compileall src/frontend_project_analysis tests
./scripts/test-smoke.sh
