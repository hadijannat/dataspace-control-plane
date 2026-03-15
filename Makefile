# Makefile — dataspace-control-plane
#
# Targets are named after the directory they exercise.
# All tests requiring live services (Temporal, Kafka, Vault, Postgres) use
# make test-gates, which passes --live-services to pytest.
#
# Quick reference:
#   make install          install all dependencies
#   make test             run all unit tests (no live services)
#   make test-gates       run release gate suites (live services required)
#   make lint             run all linters
#   make clean            remove build artifacts

.DEFAULT_GOAL := help

PYTHON ?= python3
UV     ?= uv
PNPM   ?= pnpm

# ─── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-26s %s\n", $$1, $$2}' \
	  | sort

# ─── Install ──────────────────────────────────────────────────────────────────

.PHONY: install
install: install-python install-node  ## Install all package dependencies

.PHONY: install-python
install-python:  ## Install all Python packages in editable mode (uv)
	$(UV) pip install -e core \
	  -e adapters \
	  -e procedures \
	  -e packs \
	  -e apps/control-api \
	  -e apps/temporal-workers \
	  -e apps/provisioning-agent

.PHONY: install-node
install-node:  ## Install web-console Node dependencies (pnpm)
	$(PNPM) --dir apps/web-console install

# ─── Unit / no-live-services tests ────────────────────────────────────────────

.PHONY: test
test: test-unit  ## Run all tests that do not require live services

.PHONY: test-unit
test-unit:  ## Run the full unit suite (excludes integration/chaos/tenancy/crypto markers)
	pytest -m "not (integration or chaos or tenancy or crypto)"

.PHONY: test-core
test-core:  ## Verify core/ semantic layer (unit + tenancy)
	pytest tests/unit -k core
	pytest tests/tenancy -k core

.PHONY: test-schemas
test-schemas:  ## Verify schemas/ artifact layer (unit + offline schema validation)
	pytest schemas/ -q
	pytest tests/unit -k schemas

.PHONY: test-procedures
test-procedures:  ## Verify procedures/ orchestration layer (unit + replay)
	pytest tests/unit -k procedures
	pytest tests/unit -k replay

.PHONY: test-adapters
test-adapters:  ## Verify adapters/ integration layer (pure-Python adapter tests)
	pytest tests/integration -k adapters

.PHONY: test-packs
test-packs:  ## Verify packs/ overlay layer
	pytest tests/unit -k packs
	pytest tests/integration -k packs

.PHONY: test-apps
test-apps:  ## Verify apps/ runtime surfaces
	pytest tests/integration -k apps
	pytest tests/e2e -k web_console

.PHONY: test-infra
test-infra:  ## Verify infra/ delivery substrate (helm lint + terraform validate)
	bash infra/helm/scripts/lint.sh
	@for env in infra/terraform/environments/*/; do \
	  echo "→ terraform validate $${env}"; \
	  terraform -chdir="$${env}" validate; \
	done

.PHONY: test-docs
test-docs:  ## Verify docs/ explanation layer (markdownlint + link check)
	markdownlint docs
	pytest tests/unit -k docs_links

# ─── Release gate suites (live services required) ─────────────────────────────

.PHONY: test-gates
test-gates:  ## Run all release gate suites (Temporal, Kafka, Vault, Postgres required)
	pytest tests/compatibility/dsp-tck --live-services
	pytest tests/compatibility/dcp-tck --live-services
	pytest tests/tenancy --live-services
	pytest tests/crypto-boundaries --live-services

.PHONY: test-chaos
test-chaos:  ## Run chaos tests (live services + fault-injection environment required)
	pytest tests/chaos --live-services

# ─── Lint ─────────────────────────────────────────────────────────────────────

.PHONY: lint
lint: lint-python lint-node lint-docs lint-infra  ## Run all linters

.PHONY: lint-python
lint-python:  ## Lint Python with ruff
	ruff check \
	  core adapters procedures packs \
	  apps/control-api apps/temporal-workers apps/provisioning-agent \
	  tests schemas/tools schemas/_shared/tests

.PHONY: lint-node
lint-node:  ## Lint web-console TypeScript/React with ESLint (via pnpm)
	$(PNPM) --dir apps/web-console run lint

.PHONY: lint-docs
lint-docs:  ## Lint Markdown documentation with markdownlint
	markdownlint docs

.PHONY: lint-infra
lint-infra:  ## Lint Helm charts
	bash infra/helm/scripts/lint.sh

# ─── Docs site ────────────────────────────────────────────────────────────────

.PHONY: docs-serve
docs-serve:  ## Serve the MkDocs Material docs site locally
	mkdocs serve

.PHONY: docs-build
docs-build:  ## Build the MkDocs Material docs site to site/
	mkdocs build --strict

# ─── Clean ────────────────────────────────────────────────────────────────────

.PHONY: clean
clean:  ## Remove build artifacts (__pycache__, .pytest_cache, dist, egg-info, site)
	find . -type d \( \
	  -name '__pycache__' -o \
	  -name '.pytest_cache' -o \
	  -name '*.egg-info' -o \
	  -name 'dist' -o \
	  -name '.ruff_cache' \
	) -not -path './.git/*' -exec rm -rf {} + 2>/dev/null || true
	rm -rf site
