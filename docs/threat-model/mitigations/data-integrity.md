---
title: "Mitigations: Data Integrity"
summary: "STRIDE-classified threats and mitigations for data integrity — evidence tampering, workflow history mutation, schema injection, cross-tenant disclosure, and telemetry leakage."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

Data integrity threats target the platform's regulatory audit trail, workflow history, schema contracts, and tenant data boundaries. For key management threats, see [key-management.md](key-management.md). For authentication threats, see [auth-identity.md](auth-identity.md).

## Threat Table

| ID | Threat | STRIDE | Severity | Status | Mitigation | Evidence |
|----|--------|--------|----------|--------|-----------|---------|
| T-DI-01 | Evidence artifact tampering (post-emission) | Tampering | Critical | Mitigated | Evidence envelopes are signed via Vault Transit before being written to the append-only `evidence_records` table. The Postgres role `dataspace_app` has no UPDATE or DELETE grants on `evidence_records`. Signature verification is performed by the verifier using the public key from Vault (never exported private key). | `tests/crypto-boundaries/test_evidence_signature_verification.py`; `tests/crypto-boundaries/test_no_evidence_update.py` |
| T-DI-02 | Injection via malformed ODRL policy payload | Tampering | Medium | Open | ODRL policy payloads received from external EDC connectors are validated against `schemas/odrl/source/base/policy-offer.schema.json` before being passed to the policy evaluator. Property-based tests using Hypothesis cover the parser with random inputs. However, the policy evaluator itself (Catena-X pack ODRL parser) has not yet been fuzz-tested against all possible constraint combinations. | `tests/unit/packs/parsers/test_odrl_parser.py` (partial coverage); fuzz test backlog item |
| T-DI-03 | Breaking schema change injected silently | Tampering | High | Mitigated | `diff_schema.py` classifies all schema changes against the previous git tag. Breaking changes (removed required fields, narrowed types) fail the CI gate unless a new versioned schema file exists alongside the old one. The `tests/compatibility/test_schema_meta_compliance.py` gate runs on every PR to `schemas/`. | `schemas/tools/diff_schema.py`; CI gate `make test-schemas` |
| T-DI-04 | Cross-tenant data disclosure via search or list endpoints | Information Disclosure | Critical | Mitigated | All list and search endpoints apply tenant filtering at the SQL query level using `WHERE tenant_id = <from_jwt>`. PostgreSQL RLS provides the final enforcement layer — even if the application-level filter is removed, RLS returns zero rows for unauthorized tenants. | `tests/tenancy/test_cross_tenant_isolation.py`; [auth-identity.md: T-AI-05](auth-identity.md) |
| T-DI-05 | Sensitive data (tokens, keys) exposed in OTel traces | Information Disclosure | High | Mitigated | The OTel Collector gateway applies a `redaction` processor that replaces attribute values matching patterns `.*token.*`, `.*secret.*`, `.*password.*`, `.*key.*`, and `.*authorization.*` with `[REDACTED]` before forwarding traces, metrics, and logs to Prometheus, Loki, or Tempo. HTTP request bodies are never included in spans. | `infra/observability/otel-collector/config.yaml` — `processors.redaction` section |

## Detail: T-DI-01 — Evidence Artifact Tampering

**Attack scenario**: An attacker with write access to the platform database (e.g., a compromised `dataspace_app` credential) attempts to modify an evidence envelope to remove evidence of a data exchange, falsify timestamps, or alter Annex XIII field values.

**Why the mitigation holds (two layers)**:

*Layer 1 — Cryptographic*: Each evidence envelope is signed via Vault Transit before persistence. The signature is embedded in the `proof` field of the envelope. Any modification of the envelope body after signing (payload, timestamp, actor) would invalidate the signature. Verifiers (regulators, auditors) can independently verify the signature using the public key from Vault's JWKS endpoint.

*Layer 2 — Database grant*: The Postgres role `dataspace_app` (the role used by all platform application code) has the following grants on `evidence_records`: `SELECT`, `INSERT`. It has no `UPDATE`, `DELETE`, `TRUNCATE`, or `DROP TABLE` grant. An SQL injection or compromised application credential cannot modify or delete evidence records. Only a Postgres superuser can, and application code never runs as superuser (see assumption A-09).

**Residual risk**: A Postgres superuser with physical access to the WAL can theoretically modify evidence records. This risk is accepted: (1) superuser access is restricted to DBAs, and (2) the cryptographic signature layer means that tampered records are detectable during audit verification.

## Detail: T-DI-02 — ODRL Policy Payload Injection (Open Threat)

**Attack scenario**: A Catena-X partner sends a malformed ODRL policy offer containing a crafted constraint expression (e.g., an extremely deep JSON nesting, a circular reference, or an `odrl:leftOperand` value that triggers unexpected behavior in the policy compiler).

**Current mitigation (partial)**: Schema validation against `schemas/odrl/source/base/policy-offer.schema.json` catches structurally invalid payloads. Property-based tests (`test_odrl_parser.py`) cover a range of random inputs.

**Why this is Open**: The ODRL policy evaluator in `packs/catenax/` applies constraint logic that is not yet fuzz-tested for all possible `odrl:leftOperand` and `odrl:operator` combinations. A carefully crafted policy could trigger an unhandled exception in the evaluator that propagates outside the pack boundary.

**Planned resolution**: Add Hypothesis fuzz tests covering all `odrl:leftOperand` values defined in the Catena-X policy profile. Add a `try/except` wrapper in the pack reducer that catches all evaluator exceptions and converts them to `PackConflict` errors. Target: Wave 3 hardening.
