---
title: "Mitigations: Authentication & Identity"
summary: "STRIDE-classified threats and mitigations for authentication, identity, and authorization in the dataspace control plane."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

# Mitigations: Authentication & Identity

All threats in this file are classified against the Authentication & Identity domain. For key management threats, see [key-management.md](key-management.md). For data integrity threats, see [data-integrity.md](data-integrity.md).

## Threat Table

| ID | Threat | STRIDE | Severity | Status | Mitigation | Evidence |
|----|--------|--------|----------|--------|-----------|---------|
| T-AI-01 | Operator impersonation via stolen JWT | Spoofing | High | Mitigated | Short-lived JWTs (5-minute TTL) issued by Keycloak. MFA enforced for all operator accounts in production. Keycloak session management enables token revocation before expiry. JWKS rotation is detected by `kid` mismatch in JWTs. | [ADR-0004](../../adr/0004-vault-transit-for-signing-keys.md); Keycloak realm MFA policy |
| T-AI-02 | Service account credential leakage via logs or git | Spoofing | High | Mitigated | `client_secret` values are stored in Vault at `secret/platform/*/keycloak-client-secret` and are never written to application logs, Postgres, or git-committed configuration. `tests/crypto-boundaries/key_references/test_no_raw_keys.py` scans for patterns indicating credential leakage. Secrets are rotated monthly via Vault AppRole. | `tests/crypto-boundaries/key_references/test_no_raw_keys.py` |
| T-AI-03 | JWT replay attack (reusing a valid but old token) | Spoofing | High | Mitigated | `exp` claim enforced server-side by control-api on every request (validated against current UTC time, not cached). Keycloak issues tokens with 5-minute TTL for humans and 15-minute TTL for machines. Token caching in the platform uses `exp - 60s` as the refresh threshold. | Unit tests for JWT validation in `tests/unit/apps/control_api/test_auth.py` |
| T-AI-04 | Keycloak Admin REST API exposed to unauthorized services | Elevation of Privilege | High | Mitigated | Keycloak Admin REST (port 8080/auth/admin) is restricted by Kubernetes NetworkPolicy to `provisioning-agent` pod only. Other platform pods (control-api, temporal-workers) do not have network access to the admin path. This is enforced at the network layer, not the application layer. | `infra/helm/charts/platform/templates/network-policies.yaml` — NetworkPolicy `allow-provisioning-agent-to-keycloak-admin` |
| T-AI-05 | Cross-tenant access via forged X-Tenant-ID header | Spoofing | Critical | Mitigated | PostgreSQL RLS is the final enforcement layer. Even if an attacker injects a forged `X-Tenant-ID` header that bypasses API-layer filtering, the RLS policy on all tenant tables returns zero rows for an unauthorized tenant. The RLS policy uses `current_setting('app.tenant_id')` which is set from the validated JWT `tenant_id` claim, not from the header. | `tests/tenancy/test_cross_tenant_isolation.py` — asserts zero rows returned for forged tenant ID |

## Detail: T-AI-01 — Operator Impersonation

**Attack scenario**: An attacker obtains a valid operator JWT (via phishing, session hijacking, or network interception of an HTTP connection) and uses it to call the control-api.

**Why the mitigation holds**: With a 5-minute token TTL, the attack window is narrow. Even if a token is stolen, it becomes useless within 5 minutes. MFA enforcement means that obtaining the operator's password alone is insufficient to generate a new token — the attacker would also need the TOTP device. Keycloak session management allows revocation of active sessions if compromise is detected, which also invalidates the associated refresh tokens.

**Residual risk**: A stolen token is valid for up to 5 minutes. An attacker with persistent access to the token stream (e.g., a MITM proxy) can continuously steal fresh tokens. This residual risk is accepted because: (1) all traffic is TLS-encrypted (assumption A-02 covers network-layer protection), and (2) all API calls produce audit traces with the operator's `sub` claim for forensic investigation.

## Detail: T-AI-05 — Cross-Tenant Access via Forged Header

**Attack scenario**: An authenticated operator from tenant A crafts a request with `X-Tenant-ID: tenant-B` in the header, attempting to access tenant B's data.

**Why the mitigation holds**: The control-api sets the Postgres session variable `SET LOCAL app.tenant_id = <tenant_id_from_JWT>` — it uses the validated JWT claim, not the request header. Even if the application layer erroneously used the header value, the RLS policy on the database would only return rows where `tenant_id = current_setting('app.tenant_id')`. The forged header value (tenant-B) would not match the JWT claim (tenant-A), so the session variable would still be set to tenant-A.

The `tests/tenancy/test_cross_tenant_isolation.py` suite explicitly tests this scenario by: (1) creating tenant-A and tenant-B test fixtures, (2) authenticating as tenant-A, (3) attempting a query with the tenant-B ID injected at various layers, and (4) asserting zero rows are returned for tenant-B data.
