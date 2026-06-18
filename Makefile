.PHONY: test smoke full check compile lint all

test: smoke full

smoke:
	.venv/bin/python -m pytest -m smoke

full:
	.venv/bin/python -m pytest

check: compile smoke

compile:
	python3 -m compileall src/frontend_project_analysis tests

lint:
	.venv/bin/ruff check src/frontend_project_analysis tests

all: check lint full
