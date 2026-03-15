# tests/

## Purpose

Prove the platform still works when real runtimes, real protocols, real tenant boundaries, real keys, and real failures are involved. This directory is the repo-wide verification spine — it does not own any product code; it holds the test harness, fixtures, and protocol compliance gates that span all layers.

## Quick Start

```bash
# Unit tests only — no containers, no network
pytest tests/ -m unit

# Full integration suite — requires Docker and live services
pytest tests/ --live-services

# Run only the schema compliance gate (always safe, no services)
pytest tests/compatibility/test_schema_meta_compliance.py

# Collect tests without running
pytest tests/ --collect-only -q
```

## Suite Map

| Directory | What It Tests | Marker | Service Dependencies |
|-----------|---------------|--------|----------------------|
| `tests/unit/schemas/` | JSON Schema structure, $ref validity, breaking-change detection | `unit` | None |
| `tests/unit/packs/` | ODRL parser/compiler, pack reducer, manifest validation | `unit` | None |
| `tests/unit/core/` | Domain invariants, forbidden import boundaries | `unit` | None |
| `tests/unit/adapters/` | Field mapping lineage invariants | `unit` | None |
| `tests/unit/procedures/` | State machine transitions, message validation | `unit` | None |
| `tests/integration/apps/` | Control-API HTTP layer, usage record ingestion | `integration` | FastAPI, PostgreSQL |
| `tests/integration/procedures/` | Evidence emission, compliance workflow | `integration` | Temporal, Vault |
| `tests/integration/replay/` | Temporal workflow replay from golden histories | `integration` | Temporal test server |
| `tests/integration/packs/` | Pack activation, capability registry | `integration` | None (in-process) |
| `tests/integration/adapters/` | EDC/DSP/DCP adapter wire-model validation | `integration` | EDC connector |
| `tests/compatibility/test_schema_meta_compliance.py` | JSON Schema 2020-12 meta-compliance for all source schemas | `compatibility` | None |
| `tests/compatibility/dsp-tck/` | DSP protocol TCK gate (external jar runner) | `compatibility` | DSP-facing control-api |
| `tests/compatibility/dcp-tck/` | DCP protocol TCK gate (external jar runner) | `compatibility` | Credential service, issuer, verifier |
| `tests/tenancy/postgres/` | Row-level security isolation by tenant_id | `tenancy` | PostgreSQL with RLS |
| `tests/tenancy/api/` | API layer tenant header enforcement | `tenancy` | control-api, PostgreSQL |
| `tests/tenancy/workflows/` | Temporal task queue isolation | `tenancy` | Temporal |
| `tests/tenancy/search_visibility/` | Search result scoping by tenant | `tenancy` | control-api |
| `tests/crypto-boundaries/vault_transit/` | Transit sign/verify, no raw key leakage | `crypto` | HashiCorp Vault |
| `tests/crypto-boundaries/vault_pki/` | Certificate issuance, TTL, revocation | `crypto` | HashiCorp Vault |
| `tests/crypto-boundaries/key_references/` | No PEM files in repo or schema examples | `crypto` | None (static scan) |
| `tests/crypto-boundaries/human_vs_machine_auth/` | Auth grant-type enforcement | `crypto` | Keycloak |
| `tests/crypto-boundaries/dcp_identity/` | VC/VP envelope schema presence | `crypto` | None (schema scan) |
| `tests/chaos/toxiproxy/` | Network fault injection (latency, reset, blackhole) | `chaos` | Toxiproxy, PostgreSQL, Vault, Kafka |
| `tests/chaos/workflow_recovery/` | Worker restart and history replay resilience | `chaos` | Temporal |
| `tests/chaos/dependency_loss/` | Graceful degradation when Vault is unreachable | `chaos` | Toxiproxy, Vault |
| `tests/e2e/specs/` | Browser-driven flows (login, onboarding) | `e2e` | Playwright, web-console, Keycloak |

## CI Lanes

| Lane | Markers / Suites | Trigger |
|------|-----------------|---------|
| Developer | `unit` | On every save (pre-commit) |
| PR | `unit`, `compatibility`, schema meta-compliance | On every PR push |
| Nightly | All markers including `integration`, `tenancy`, `crypto`, `chaos`, `slow`, `nightly` | Scheduled 02:00 UTC |
| Release | All markers + DSP/DCP TCK + explicit `--live-services` | On release branch tag |

## Rules

- No test in `unit/` opens a socket. Imports that require network access must be `pytest.importorskip`'d and the test skipped with a clear message.
- No test in `tenancy/` runs as PostgreSQL superuser unless explicitly testing the superuser bypass invariant, and those tests must be documented with a "never run application code as superuser" comment.
- No test in `crypto-boundaries/` reaches raw key material. Vault Transit keys must never appear in test output, logs, or fixtures. Assert that the API response never contains `private_key` at the top level.
- All integration/tenancy/crypto/chaos tests must be decorated with the appropriate marker and skip cleanly when `--live-services` is not passed.
