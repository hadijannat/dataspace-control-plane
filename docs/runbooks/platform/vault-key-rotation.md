---
title: "Vault Key Rotation"
summary: "Procedure for rotating the Vault Transit signing key with a non-disruptive key version window, including pre-rotation verification and post-rotation validation."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P3"
affected_services:
  - temporal-workers
  - provisioning-agent
status: approved
---

# Vault Key Rotation

## When to Run This Procedure

- **Scheduled rotation**: Quarterly key rotation per security policy.
- **Incident-triggered rotation**: Immediately following a suspected key compromise or unauthorized signing operation detected in the Vault audit log.
- **Post-breach rotation**: After any security incident that may have exposed Vault credentials (even if key exportability is false, an unauthorized signing operation requires immediate rotation).

## Pre-Rotation Checklist

Before rotating:

- [ ] Verify the current signing key is working: test sign and verify with a known payload
- [ ] Ensure no DPP export workflows are in progress (key rotation mid-export is safe but adds complexity)
- [ ] Note the current key version: `vault read transit/keys/dataspace-signing | grep latest_version`
- [ ] Record the pre-rotation key ID and timestamp in the incident ticket or rotation log
- [ ] Ensure Vault audit logging is enabled: `vault audit list`

## Rotation Procedure

### Step 1: Verify current signing key works

```bash
# Test sign with the current key
vault write transit/sign/dataspace-signing \
  input=$(echo -n "pre-rotation-test-payload" | base64) \
  signature_algorithm=pkcs1v15

# Note the signature and key_version in the response
# signature: vault:v<VERSION>:...
```

### Step 2: Rotate the Transit key

```bash
# Rotate the signing key to a new version (non-disruptive — old version remains for verification)
vault write -f transit/keys/dataspace-signing/rotate

# Verify the new version is now the latest
vault read transit/keys/dataspace-signing
# Look for: latest_version = <NEW_VERSION>
# Also check: min_decryption_version (old versions still valid for verification)
```

### Step 3: Verify new key version is used for new signatures

```bash
# Sign a test payload — should use the new key version
vault write transit/sign/dataspace-signing \
  input=$(echo -n "post-rotation-test-payload" | base64) \
  signature_algorithm=pkcs1v15

# Verify the signature version in the response: vault:v<NEW_VERSION>:...
```

### Step 4: Verify old signatures still verify

```bash
# Use the signature captured in Step 1 (pre-rotation)
vault write transit/verify/dataspace-signing \
  input=$(echo -n "pre-rotation-test-payload" | base64) \
  signature="vault:v<OLD_VERSION>:<SIGNATURE_FROM_STEP_1>"

# Expected response: valid = true
```

This confirms that existing signed artifacts (VCs, evidence envelopes, DID documents) remain verifiable with the old key version while new artifacts use the new key version.

### Step 5: Update key version preference (optional — for strict rotation)

If the rotation policy requires that the old key version cannot be used for new signing (only for verification):

```bash
# Set min_encryption_version to the new version (old version can still verify, cannot sign)
vault write transit/keys/dataspace-signing/config \
  min_encryption_version=<NEW_VERSION>
```

!!! warning "Do not set min_decryption_version yet"
    Setting `min_decryption_version` to the new version would prevent verification of artifacts signed with the old key. Only set this after the rotation window (typically 30 days) during which all previously signed artifacts should have been re-signed if needed.

### Step 6: Update Terraform state if key config is Terraform-managed

If the Vault key configuration (`min_encryption_version`, `min_decryption_version`, `deletion_allowed`) is managed by Terraform:

```bash
cd infra/terraform/roots/platform
terraform import vault_transit_secret_backend_key.dataspace_signing dataspace-signing
terraform plan -target=vault_transit_secret_backend_key.dataspace_signing
terraform apply -target=vault_transit_secret_backend_key.dataspace_signing
```

Update the key version values in `infra/terraform/roots/platform/vault.tf` to match the new rotation state.

### Step 7: Restart temporal-workers to pick up new key version

The Vault adapter in temporal-workers caches the key version. Restart to clear the cache:

```bash
kubectl rollout restart deployment/temporal-workers -n dataspace-platform
kubectl rollout status deployment/temporal-workers -n dataspace-platform
```

### Step 8: Verify signing continues to work in production

```bash
# Check temporal-worker logs for any signing errors after restart
kubectl logs deployment/temporal-workers -n dataspace-platform --tail=50 | grep -E "vault|signing|error"

# Check Vault audit log for recent signing operations (should show new key version)
kubectl exec -it vault-0 -n dataspace-infra -- \
  tail -5 /vault/audit/audit.log | python3 -m json.tool | grep "key_version"
```

Expected: `"key_version": <NEW_VERSION>` in recent signing operations.

## Post-Rotation Evidence Record

Record the following in the rotation log (incident ticket or internal audit tracker):

| Field | Value |
|-------|-------|
| Pre-rotation key version | v`<OLD_VERSION>` |
| Post-rotation key version | v`<NEW_VERSION>` |
| Rotation timestamp | `<ISO 8601 timestamp>` |
| Operator who performed rotation | `<name>` |
| Old version min_decryption still valid? | Yes (until rotation window expires) |
| Terraform state updated? | Yes / No (manual) |
| Verification test passed? | Yes |
| temporal-workers restarted? | Yes |

## Deprecating the Old Key Version (30 Days Post-Rotation)

After the rotation window (default: 30 days):

```bash
# Set min_decryption_version to prevent verification with the old key
# Only do this after confirming no artifacts signed with the old version need re-verification
vault write transit/keys/dataspace-signing/config \
  min_decryption_version=<NEW_VERSION>
```

## Related Runbooks

- [Vault Transit Failures](../incidents/vault-transit-failures.md) — if signing failures occur after rotation
- [Certificate Renewal](certificate-renewal.md) — if Vault PKI certificates also need renewal
