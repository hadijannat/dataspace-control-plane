---
title: "11. Risks and Technical Debt"
summary: "Current risk register and technical debt inventory for the dataspace control plane."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

## Current Risk Register

Risks are tracked here until mitigated. Each risk has a probability (High/Medium/Low), impact (High/Medium/Low), current mitigation status, and an owning lead. Risks marked `probability: High` are escalated in the next wave planning session.

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|-------------|--------|-----------|-------|
| R-01 | **Upstream vendor artifacts pending SHA-256 pin** — AAS Release 25-01, ODRL 2.2, W3C VC 2.0 upstream artifacts are not yet pinned with `provenance.json`. CI will not catch an artifact change. | High | Medium | Run `pin_upstream.py` for each family; CI gate `test_provenance_present` blocks merge without SHA-256. Tracked in `schemas/CLAUDE.md`. | schemas-lead |
| R-02 | **No release gate for DSP/DCP TCK** — `tests/compatibility/dsp-tck/` and `tests/compatibility/dcp-tck/` stubs are created but the TCK protocol surfaces are not yet wired to a real EDC counterparty. | High | High | TCK directories scaffolded; need TCK test artifacts from Eclipse Foundation + running EDC counterparty in staging. Required before first Catena-X production participation. | tests-lead |
| R-03 | **Temporal namespace not bootstrapped** — The platform requires a `dataspace` Temporal namespace. No bootstrap Job or `temporalctl` step exists in `infra/`. | Medium | High | Add a Kubernetes Job or Helm post-install hook that runs `temporal operator namespace create dataspace` against the Temporal Server endpoint. | infra-lead |
| R-04 | **ESPR delegated acts not yet published** — EU Regulation 2024/1781 delegated acts for specific product categories are pending publication. `packs/espr_dpp/delegated_acts/` holds a template that must be updated when acts publish. | Medium | High | Template structure is correct; monitor EUR-Lex for publication. When acts publish, update field definitions and run `tests/unit/packs/validators/test_espr_dpp_validators.py`. | packs-lead |
| R-05 | **No integration tests for adapters** — `tests/integration/adapters/` stub directories exist but no adapter integration tests are written. Adapter correctness is verified only by unit tests with mocks. | Medium | Medium | Wire integration test containers (WireMock for DSP/DCP, BaSyx container for AAS, Keycloak test container) once adapters are scaffolded. | adapters-lead |
| R-06 | **Vault PKI not wired into Helm chart pod annotations** — The Vault PKI issuer is defined in Terraform but pod annotations for cert-manager Vault issuer + ServiceAccount + VaultAuth are not yet in the Helm charts. | Medium | High | Add Vault agent injector annotations or cert-manager `Certificate` objects to each Deployment. Required before TLS verification tests pass. | infra-lead |
| R-07 | **edc-extension is Java in a Python monorepo** — `apps/edc-extension/` requires Java 17+ and Maven/Gradle build tooling. This creates a build dependency not shared by other apps. | Low | Medium | Isolate EDC extension build in its own Docker build stage. Add `make build-edc-extension` target using a Java builder image. | apps-lead |
| R-08 | **Web-console has no authentication state management** — The Next.js web-console must handle Keycloak Authorization Code flow, token refresh, and logout. Without this, the console cannot authenticate operators. | Medium | High | Implement NextAuth.js with Keycloak provider or use Keycloak's built-in JavaScript adapter. Must handle PKCE and silent refresh. | apps-lead |

## Technical Debt Inventory

Technical debt items are known shortcuts that must be addressed before production readiness. They are not risks (they will not cause failures in the short term) but will increase maintenance cost if left unaddressed.

| # | Debt | Location | Effort | Priority |
|---|------|---------|--------|---------|
| TD-01 | **Empty `bundles/` and `derived/` in schemas/** — No Redocly bundle step or derive script has been run. Generated artifacts are missing. | `schemas/*/bundles/`, `schemas/*/derived/` | S | High |
| TD-02 | **No root `Makefile`** — Each layer needs a `make test-<dir>` target but the root Makefile does not exist. Build commands are documented but not automated. | `/Makefile` | S | High |
| TD-03 | **No `pyproject.toml` at repo root** — The repo uses per-layer Python code but has no root-level `pyproject.toml` or `uv.lock` to manage shared dependencies and dev tooling. | `/pyproject.toml` | S | High |
| TD-04 | **Procedure stubs only** — `procedures/` has directory scaffolding but no workflow implementations. All procedure tests use mocks against stub interfaces. | `procedures/` | XL | High |
| TD-05 | **App entrypoints are stubs** — `apps/control-api/`, `apps/temporal-workers/`, and `apps/web-console/` are scaffolded but contain no implementation. The OpenAPI spec in `docs/api/openapi/source/control-api.yaml` is the target contract. | `apps/` | XL | High |
| TD-06 | **No OpenTelemetry instrumentation** — No OTLP spans are emitted by any current code. Observability is designed but not implemented. | `apps/`, `adapters/` | M | Medium |
| TD-07 | **`docs/generated/` directory not populated** — `generate_docs.py` exists in `schemas/tools/` but has not been run. Schema index and cross-reference docs are missing. | `docs/generated/` | S | Low |
