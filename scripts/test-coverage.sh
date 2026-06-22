#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
UV_CACHE_DIR=${UV_CACHE_DIR:-/private/tmp/uv-cache} .venv/bin/python -m coverage run -m pytest
UV_CACHE_DIR=${UV_CACHE_DIR:-/private/tmp/uv-cache} .venv/bin/python -m coverage report --show-missing
