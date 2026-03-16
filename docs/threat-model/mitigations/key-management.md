---
title: "Mitigations: Key Management"
summary: "STRIDE-classified threats and mitigations for cryptographic key management — key extraction, git commitment, rotation failure, Vault DoS, and certificate revocation."
owner: docs-lead
last_reviewed: "2026-03-14"
status: approved
---

Key management threats target the platform's cryptographic boundary: the Vault Transit engine and PKI issuer. For authentication threats that use the same keys, see [auth-identity.md](auth-identity.md). The Vault Transit ADR is [ADR-0004](../../adr/0004-vault-transit-for-signing-keys.md).

## Threat Table

| ID | Threat | STRIDE | Severity | Status | Mitigation | Evidence |
|----|--------|--------|----------|--------|-----------|---------|
| T-KM-01 | Private signing key extracted from Vault | Information Disclosure | Critical | Mitigated | All signing keys are created with `exportable=false` and `allow_plaintext_backup=false`. There is no Vault API call that can return the raw private key material for a non-exportable Transit key. The Vault audit backend logs every `transit/sign` and `transit/verify` operation with the caller's Vault token identity — unauthorized signing attempts are auditable. | `tests/crypto-boundaries/vault_transit/test_no_key_export.py` — asserts that `vault read transit/export/signing-key/dataspace-signing` returns an error |
| T-KM-02 | Signing key committed to git repository | Information Disclosure | Critical | Mitigated | No `.pem`, `.key`, `.p12`, or `.pfx` files are present in the repository. The `tests/crypto-boundaries/key_references/test_no_pem_files_committed_to_repo.py` gate scans all git-tracked files for these extensions. All test keys used in unit tests are ephemeral (generated during test setup, not committed) or are clearly labeled as fake test fixtures with no cryptographic validity. | `tests/crypto-boundaries/key_references/test_no_pem_files_committed_to_repo.py` |
| T-KM-03 | Signing key not rotated after compromise | Elevation of Privilege | High | Mitigated | The quarterly key rotation procedure (`docs/runbooks/platform/vault-key-rotation.md`) defines the rotation steps including a rotation window during which old key versions remain valid for verification but not for new signing. Vault key versioning (`min_encryption_version`) enforces the rotation boundary. Incident-triggered rotation is mandatory after any suspected key compromise. | [Vault Key Rotation runbook](../../runbooks/platform/vault-key-rotation.md); Vault audit log |
| T-KM-04 | Vault sealed during signing operations (DoS) | Denial of Service | High | Mitigated | Vault HA mode (3-node Raft cluster) is required for staging and production environments. Auto-unseal via cloud KMS (AWS KMS / GCP Cloud KMS) prevents seal after pod restarts. The `tests/chaos/dependency_loss/test_vault_seal_graceful_failure.py` chaos test verifies that signing failures are surfaced as retriable Temporal activity errors (not silent failures) and that the platform fails gracefully without data corruption. | `tests/chaos/dependency_loss/test_vault_seal_graceful_failure.py`; [arc42/07: Deployment View](../../arc42/07-deployment-view.md) — Vault StatefulSet HA config |
| T-KM-05 | Ephemeral certificate used after revocation | Spoofing | Medium | Mitigated | Platform-issued TLS certificates have short TTLs (24-hour for internal service certs, 90-day for external TLS). The Vault PKI CRL endpoint is configured and checked by all services using TLS client authentication. cert-manager handles automatic renewal 30 days before expiry. Revoked certificates are published to the CRL within 5 minutes of revocation. | `infra/helm/charts/platform/values.yaml` — cert-manager CRL check configuration; [Certificate Renewal runbook](../../runbooks/platform/certificate-renewal.md) |

## Detail: T-KM-01 — Private Key Extraction

**Attack scenario**: An attacker who has obtained a valid Vault token (e.g., via a stolen AppRole credential or an overly permissive Vault policy) attempts to extract the raw private key material by calling `vault read transit/export/signing-key/dataspace-signing`.

**Why the mitigation holds**: When a Transit key is created with `exportable=false`, the Vault API returns an error for all export operations regardless of the caller's token policy:

```text
Error reading transit/export/signing-key/dataspace-signing: Error making API request.
Code: 403. Errors:
* exportable must be set to export a key
```

This is enforced at the Vault core level — no policy can override `exportable=false` because the flag is set on the key, not the policy. The private key material exists only within Vault's encrypted storage backend (Raft with AES-256-GCM encryption). It cannot be retrieved via the API regardless of the caller's privilege level.

**Residual risk**: A Vault node with physical or root-level filesystem access could theoretically extract the Raft storage. This risk is mitigated by: (1) Vault storage is encrypted at rest with a separate encryption key managed by the cloud KMS, (2) Vault nodes run in isolated Kubernetes pods with no host filesystem access, and (3) the cloud KMS key that decrypts Vault storage is access-controlled separately from the platform's Vault credentials.

## Detail: T-KM-04 — Vault Sealed During Signing (Graceful Failure)

**Attack scenario**: A brief Vault availability disruption (pod restart, network partition, KMS unavailability) seals Vault while a Temporal workflow activity is attempting to sign an evidence envelope.

**Why the mitigation holds (defense-in-depth)**:

1. **Vault HA**: 3-node Raft cluster means a single node failure does not seal the cluster. A quorum of 2 nodes remains operational.
2. **Auto-unseal**: Cloud KMS-based auto-unseal means that pod restarts (the most common seal trigger in Kubernetes) cause a brief pause but not a permanent seal.
3. **Temporal retry**: The signing activity in `temporal-workers` is configured with `RetryPolicy(maximum_attempts=10, initial_interval=5s, backoff_coefficient=2.0)`. A brief Vault outage (< 85 seconds in the worst case with 10 retries) is transparent to the workflow — it simply retries after each Vault error.
4. **Chaos test**: `tests/chaos/dependency_loss/test_vault_seal_graceful_failure.py` simulates a Vault seal during a signing activity and asserts that: (a) the activity fails with a retriable error (not a fatal error), (b) the Temporal workflow does not enter a FAILED state until all retries are exhausted, and (c) no partial state is written (evidence is either fully signed or not written at all).
