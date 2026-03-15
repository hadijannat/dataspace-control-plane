---
title: "Vault Transit for all signing operations — no raw private key material in application state"
status: accepted
date: 2026-03-14
decision-makers:
  - infra-lead
  - procedures-lead
  - core-lead
consulted:
  - adapters-lead
  - tests-lead
  - all-leads
informed:
  - all-leads
---

# Vault Transit for all signing operations

## Context and Problem Statement

The platform must sign Verifiable Credentials (W3C VC 2.0 Data Integrity proofs), DID documents, ODRL agreement seals, and evidence envelopes. These signed artifacts are the cryptographic foundation of the audit trail: a tampered evidence envelope must be detectable by signature verification.

The signing key management strategy determines the blast radius of a key compromise event. If signing keys are stored in Postgres alongside the data they sign, a database breach exposes both the data and the ability to forge new signed artifacts — making the tamper-evident trail meaningless. If keys are stored in application code or configuration, a container image pull or config leak achieves the same.

The platform operates in a multi-tenant environment where different tenants may eventually require separate signing keys (for DID document separation). Key rotation must be non-disruptive: existing signed artifacts must remain verifiable while new artifacts use the new key version.

## Decision Drivers

* Key custody boundary: private keys must never appear in application state, Temporal workflow history, Postgres rows, or application logs
* No raw key in state or transmission: the signing API must accept payload and return signature without transmitting or returning the private key
* Rotation support: key rotation must be possible without re-signing all existing artifacts — old key versions must remain valid for verification during a rotation window
* Audit logging of signing operations: every signing request must be logged with caller identity, key ID, and timestamp without exposing the key material
* Multi-tenant key isolation: different tenants must be able to have different signing keys (future requirement)
* Infrastructure already available: the platform requires Vault for Keycloak secret storage and certificate management — adding Transit is an extension of an existing dependency, not a new one

## Considered Options

* HashiCorp Vault Transit engine (chosen)
* AWS KMS
* GCP Cloud KMS
* Software keystore in Postgres (BYTEA column with application-level AES-GCM wrapping)

## Decision Outcome

**Chosen option: "HashiCorp Vault Transit engine"**, because Vault is already a required infrastructure dependency for PKI and Keycloak secret storage; Transit adds signing capability without introducing a new vendor. Keys are created with `exportable=false` and `allow_plaintext_backup=false` — there is no API call that can retrieve the private key material. The Vault audit backend logs every `transit/sign` and `transit/verify` operation with the caller's Vault token identity, the key name, and the key version used — providing a complete key usage trail for compliance audits. Key rotation is performed via `vault write -f transit/keys/{key_name}/rotate`, after which new signatures use the new key version while old signatures remain verifiable using the appropriate previous version.

### Positive Consequences

* Keys never leave Vault: no API call can extract `exportable=false` keys — eliminates the key exfiltration threat class
* Vault audit log is the key usage trail: every signing operation is logged with caller identity without application-level audit code
* Key rotation window: `min_decryption_version` controls which old key versions remain valid; rotation is non-disruptive
* Infrastructure consistency: Vault is already deployed for PKI and Keycloak secrets — no new vendor or deployment
* `tests/crypto-boundaries/vault_transit/` suite verifies the Transit invariants (no export, key version tracking)

### Negative Consequences

* Vault availability is now on the critical path for all signing operations: if Vault is sealed or unavailable, no VC can be issued, no evidence can be signed, and DPP export workflows stall. See Risk R-04 and runbooks/incidents/vault-transit-failures.md.
* Vault Transit API latency adds to signing operation time (target: P95 < 100ms — see arc42/10). High-volume signing (bulk DPP export) requires connection pooling in the Vault adapter.
* Multi-tenant key isolation (separate signing key per tenant) is supported by Transit's key namespace but requires per-tenant key provisioning during onboarding — adds steps to the OnboardingWorkflow.

### Confirmation

* `tests/crypto-boundaries/vault_transit/test_no_key_export.py`: asserts that calling `vault read transit/export/signing-key/{key_name}` returns an error (key not exportable)
* `tests/crypto-boundaries/key_references/test_no_raw_keys.py`: scans workflow history snapshots and Postgres fixtures for patterns matching PEM-encoded keys
* `tests/crypto-boundaries/key_references/test_no_pem_files_committed_to_repo.py`: scans git-tracked files for `.pem`, `.key`, `.p12` extensions

## Pros and Cons of the Options

### HashiCorp Vault Transit Engine

Vault secrets engine providing sign/verify/encrypt/decrypt operations. Keys are stored in Vault's encrypted storage backend and never exported.

* Good, because `exportable=false` makes key extraction architecturally impossible via API
* Good, because Vault audit log provides key usage trail without application-level code
* Good, because key rotation with version window is built in
* Good, because already a required dependency — no new vendor
* Good, because supports RSA-PSS, ECDSA P-256, Ed25519 — all needed for VC proofs
* Bad, because Vault unavailability blocks signing — requires Vault HA in production
* Bad, because Transit API latency (typically 5-20ms per operation) must be accounted for in SLOs

### AWS KMS

AWS-managed key management service with signing support.

* Good, because fully managed — no KMS server to operate
* Good, because high availability by default
* Good, because supports ECDSA P-256 and RSA-PSS for VC signing
* Bad, because AWS vendor lock-in — platform must run on AWS or replicate KMS API
* Bad, because no offline/air-gapped support — unsuitable for disconnected environments
* Bad, because adds AWS SDK dependency to the signing adapter

### GCP Cloud KMS

Google Cloud-managed key management service.

* Good, because fully managed, high availability
* Bad, because GCP vendor lock-in
* Bad, because same offline/air-gapped limitation as AWS KMS
* Bad, because Python GCP SDK adds a heavyweight dependency

### Software Keystore in Postgres

Store wrapped private keys in Postgres using application-level AES-GCM encryption. Wrapping key stored in environment variable or Vault secret.

* Good, because no additional infrastructure — Postgres is already required
* Bad, because wrapped key in Postgres means a database breach could expose the wrapping key + wrapped key together — defeating the isolation purpose
* Bad, because no audit log of signing operations without custom application code
* Bad, because key rotation requires re-signing all existing artifacts or maintaining a key version lookup table
* Bad, because private key material passes through application memory during signing, increasing exposure window
