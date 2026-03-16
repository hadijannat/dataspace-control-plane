---
title: "Threat Model: Security Assumptions"
summary: "Security assumptions that must hold for the threat model mitigations to be valid. Violations are P1 security incidents."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

The following assumptions must hold for the threat model mitigations documented in this section to be valid. If any assumption is violated, the associated mitigations may not hold and the threat must be re-evaluated.

**Any assumption violation must be treated as a P1 security incident and escalated to infra-lead immediately.**

## Infrastructure Assumptions

**A-01**: Vault is correctly initialized, unsealed, and has audit logging enabled before platform startup. The Vault audit backend forwards to a SIEM outside the cluster. If Vault audit logging is disabled, the key usage trail (mitigations T-KM-01 through T-KM-05) cannot be verified.

**A-02**: Network policies restrict Vault API (port 8200) and Keycloak Admin REST (port 8080/admin) to pods in the `dataspace-platform` namespace only. External or cross-namespace access to these ports is blocked by Kubernetes NetworkPolicy objects in `infra/helm/charts/platform/templates/network-policies.yaml`.

**A-03**: PostgreSQL is not reachable from outside the Kubernetes cluster. No external load balancer or ingress routes to Postgres port 5432. The RLS mitigation (T-DI-04, T-AI-05) is the final defense layer — if Postgres is reachable externally, the defense-in-depth model is reduced.

**A-04**: OTel Collector network policy blocks external access to ports 4317 (OTLP gRPC) and 4318 (OTLP HTTP). The Collector's redaction processor (T-DI-05) blocks token/key/password patterns before export — if the Collector is bypassed or the raw OTLP stream is intercepted, redaction does not apply.

**A-05**: Vault audit logging is enabled and forwarded to the SIEM. Vault Transit key export is set to `exportable=false` for all signing keys. These settings are applied by Terraform and must not be manually overridden.

**A-06**: Temporal gRPC (port 7233) is not exposed via ingress. The Temporal UI (port 8080) is accessible only via VPN-restricted ingress or Kubernetes port-forward. Temporal workflow history contains no sensitive material (credentials, personal data) per the workflow code review process.

**A-07**: Base container images in release builds are pinned to SHA-256 digests (not `:latest` tags). The image pull policy is `IfNotPresent` with digest pinning in production. Unpinned images can introduce unexpected code changes that bypass the signing boundary.

**A-08**: Keycloak realm configuration is managed exclusively by Terraform and the provisioning-agent. Manual changes to realms, clients, or redirect URIs in the Keycloak admin console are prohibited without a corresponding Terraform change. Terraform state drift is detected by `terraform plan` in CI on every PR to `infra/terraform/roots/platform/`.

## Application Assumptions

**A-09**: Application pods run as non-superuser Postgres roles. The database role `dataspace_app` has SELECT, INSERT, UPDATE, DELETE grants on tenant tables but no DDL, TRUNCATE, or superuser grants. RLS policies on all tenant tables are enforced for this role.

**A-10**: Temporal workflow code does not log, persist, or include in workflow input/output any of the following: Keycloak client_secrets, Vault tokens, raw private key material, or unredacted personal data. This is enforced by code review and by the `tests/crypto-boundaries/key_references/test_no_raw_keys.py` gate.

**A-11**: The `control-api` validates JWT signatures against Keycloak's JWKS endpoint before trusting any claim. The `tenant_id` claim in the JWT is used as the RLS session variable — the API layer does not accept a tenant ID from request headers as authoritative.

**A-12**: The `Idempotency-Key` header is not treated as a security control. It is a client convenience feature only. Idempotency keys cannot be used to bypass authentication or authorization.

## External Dependency Assumptions

**A-13**: The EU DPP registry API endpoint is a trusted external service operated by the EU. Responses from the registry are treated as authoritative for submission status but are validated against the DPP registry response schema before being persisted.

**A-14**: Catena-X partner EDC connectors present valid W3C VCs issued by a trusted Catena-X CA. The platform verifies the VC signature against the issuer's DID document before accepting a DCP credential presentation. Unverified or expired credentials are rejected.

**A-15**: The Catena-X network infrastructure (DSP broker, DID registry) is not controlled by the platform and may be subject to its own security vulnerabilities. Platform-side mitigations (rate limiting, VC verification, ODRL schema validation) are the first defense against malformed inputs from the Catena-X network.
