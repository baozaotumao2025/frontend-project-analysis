.PHONY: test smoke e2e e2e-install e2e-flow e2e-reset full check compile lint all

test: smoke full

smoke:
	.venv/bin/python -m pytest -m smoke

e2e:
	./scripts/test-e2e.sh

e2e-install:
	./scripts/test-e2e-install.sh

e2e-flow:
	./scripts/test-e2e-flow.sh

e2e-reset:
	./scripts/test-e2e-reset.sh

full:
	.venv/bin/python -m pytest

check: compile smoke

compile:
	python3 -m compileall src/frontend_project_analysis tests

lint:
	.venv/bin/ruff check src/frontend_project_analysis tests

all: check lint full
