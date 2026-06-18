#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
./scripts/test-check.sh
./scripts/test-full.sh
