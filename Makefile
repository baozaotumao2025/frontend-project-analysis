.PHONY: help test quality release e2e \
	test.smoke test.full test.check test.e2e test.e2e-install test.e2e-flow test.e2e-reset \
	quality.compile quality.lint \
	release.preflight release.packet release.card release.publish release.all \
	smoke full check compile lint all e2e e2e-install e2e-flow e2e-reset \
	release release-card release-preflight release-llm-review release-publish

help:
	@printf '%s\n' \
		'Groups:' \
		'  make test               Run smoke and full test suites' \
		'  make quality            Run compile and lint checks' \
		'  make release            Run the review packet chain' \
		'  make release.publish    Run the maintainer publish flow' \
		'  Primary grouped targets use dotted names; hyphenated names are compatibility aliases' \
		'' \
		'Testing targets:' \
		'  make test.smoke         Run smoke tests' \
		'  make test.full          Run the full test suite' \
		'  make test.check         Run compile plus smoke checks' \
		'  make test.e2e           Run default E2E suite' \
		'  make test.e2e-install   Run install-focused E2E suite' \
		'  make test.e2e-flow      Run workflow recovery E2E suite' \
		'  make test.e2e-reset     Run reset-focused E2E suite' \
		'' \
		'Quality targets:' \
		'  make quality.compile    Run compileall over src/ and tests/' \
		'  make quality.lint       Run Ruff over src/ and tests/' \
		'' \
		'Release targets:' \
		'  make release.preflight  Run deterministic release checks' \
		'  make release.packet      Generate the full release review packet' \
		'  make release.card        Generate the minimal reviewer card' \
		'  make release.publish     Run tests, review, version checks, commit, tag, and push' \
		'  make release.all         Run preflight plus review packet generation' \
		'' \
		'Compatibility aliases:' \
		'  make smoke              Alias for make test.smoke' \
		'  make full               Alias for make test.full' \
		'  make check              Alias for make test.check' \
		'  make compile            Alias for make quality.compile' \
		'  make lint               Alias for make quality.lint' \
		'  make all                Alias for compile, lint, and full' \
		'  make e2e                Alias for make test.e2e' \
		'  make e2e-install        Alias for make test.e2e-install' \
		'  make e2e-flow           Alias for make test.e2e-flow' \
		'  make e2e-reset          Alias for make test.e2e-reset' \
		'  make release            Alias for make release.all' \
		'  make release-card       Alias for make release.card' \
		'  make release-preflight  Alias for make release.preflight' \
		'  make release-llm-review  Alias for make release.packet' \
		'  make release-publish    Alias for make release.publish'

test: test.smoke test.full

quality: quality.compile quality.lint

release: release.all

e2e: test.e2e

test.smoke:
	.venv/bin/python -m pytest -m smoke

test.full:
	.venv/bin/python -m pytest

test.check:
	python3 -m compileall src/frontend_project_analysis tests
	.venv/bin/python -m pytest -m smoke

test.e2e:
	./scripts/test-e2e.sh

test.e2e-install:
	./scripts/test-e2e-install.sh

test.e2e-flow:
	./scripts/test-e2e-flow.sh

test.e2e-reset:
	./scripts/test-e2e-reset.sh

quality.compile:
	python3 -m compileall src/frontend_project_analysis tests

quality.lint:
	.venv/bin/ruff check src/frontend_project_analysis tests

release.preflight:
	./scripts/release-preflight.sh

release.packet:
	./scripts/release-llm-review.sh

release.card:
	./scripts/release-card.sh

release.publish:
	./scripts/release-publish.sh

release.all:
	./scripts/release.sh

smoke: test.smoke

full: test.full

check: test.check

compile: quality.compile

lint: quality.lint

all: test.check quality.lint test.full

e2e-install: test.e2e-install

e2e-flow: test.e2e-flow

e2e-reset: test.e2e-reset

release-preflight: release.preflight

release-llm-review: release.packet

release-card: release.card

release-publish: release.publish
