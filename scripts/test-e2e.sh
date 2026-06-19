#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
UV_CACHE_DIR=${UV_CACHE_DIR:-/private/tmp/uv-cache} .venv/bin/python -m pytest -m "${E2E_MARKS:-e2e}" tests/test_cli_e2e.py -q
