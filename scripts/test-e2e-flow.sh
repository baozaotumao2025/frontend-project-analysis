#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
E2E_MARKS=e2e_flow ./scripts/test-e2e.sh
