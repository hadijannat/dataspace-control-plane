---
title: "Vault Transit Failures"
summary: "Runbook for diagnosing and recovering from Vault Transit signing failures — sealed Vault, expired tokens, revoked policies, or network partitions."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P1"
affected_services:
  - temporal-workers
  - provisioning-agent
status: approved
---

## Trigger / Alert Source

- **Alert names**: `VaultTransitSigningFailureRate`, `VaultSealedAlert`, `VaultUnreachable`
- **Alert conditions**: `rate(vault_transit_sign_errors_total[5m]) > 0.1` OR `vault_core_unsealed == 0`
- **Manual trigger**: Temporal workers log `403 Forbidden` or `connection refused` errors when calling Vault API; workflows in `OnboardingWorkflow` or `DPPExportWorkflow` fail at signing activities
- **Typical symptom**: Multiple Temporal workflows stuck at `sign_did_document` or `sign_evidence_envelope` activities; Vault UI shows "Vault is sealed" banner

## Scope and Blast Radius

**Affected when Vault Transit is unavailable:**

- **temporal-workers**: All signing activities fail. `OnboardingWorkflow` cannot sign DID documents. `DPPExportWorkflow` cannot sign evidence envelopes. Workflows stall in RUNNING state (Temporal retries activities with exponential backoff until Vault recovers).
- **provisioning-agent**: Cannot sign Gaia-X Self-Descriptions. Connector registration that requires signed artifacts fails.
- **control-api**: Unaffected for reads. New VC issuance workflows (if any) fail when they reach signing activities.

**NOT affected:**

- **Postgres reads and writes**: Independent of Vault.
- **Keycloak authentication**: Independent of Vault Transit (Keycloak uses its own keystore for JWT signing).
- **Temporal workflow scheduling**: Temporal Server itself continues running; activities are queued for retry.

**Data loss risk**: None — signing is a side-effect-free operation (read-only from the data perspective). Workflows retry the signing activity automatically. No data is lost.

## Pre-Checks

```bash
# Check Vault pod status
kubectl get pods -n dataspace-infra | grep vault

# Check Vault seal status
kubectl exec -it vault-0 -n dataspace-infra -- vault status

# Check Vault pod logs for errors
kubectl logs vault-0 -n dataspace-infra --tail=50

# Check Temporal worker logs for Vault errors
kubectl logs deployment/temporal-workers -n dataspace-platform --tail=100 | grep -i "vault\|signing\|forbidden\|403"
```

## Communication Steps

| Time | Action | Channel | Audience |
|------|--------|---------|---------|
| Immediately | Acknowledge the alert | PagerDuty | On-call |
| +2 min | Post in `#platform-incidents`: "Vault signing failures — investigating seal/policy issue" | Slack | Platform team |
| +10 min (if unresolved) | Page infra-lead | PagerDuty | infra-lead |
| +15 min | If Vault is sealed: contact the 3 unseal key holders via secure channel | Out-of-band | Vault key holders |

## Triage Checklist

1. [ ] Is Vault sealed? (`vault status` → `Sealed: true`)
2. [ ] Is Vault reachable from the platform namespace? (network policy issue?)
3. [ ] Is the Vault token used by temporal-workers expired or revoked?
4. [ ] Has a Vault policy been modified recently that revoked the `dataspace-signer` policy?
5. [ ] Is the Transit key itself disabled or deleted?

## Investigation Steps

### Step 1: Check Vault seal status

```bash
kubectl exec -it vault-0 -n dataspace-infra -- vault status
```

**If `Sealed: true`**: Vault is sealed — see Scenario A.
**If `Sealed: false`**: Vault is unsealed — proceed to Step 2.

### Step 2: Check Vault AppRole token validity

```bash
# Check the token used by temporal-workers
# (token is stored in Vault at secret/data/platform/temporal-workers/vault-token)
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault token lookup <TOKEN_FROM_SECRET>
```

Look for `expire_time` — if it is in the past, the token has expired. See Scenario B.

### Step 3: Check Transit key status

```bash
# List Transit keys
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault list transit/keys

# Check the dataspace-signing key details
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault read transit/keys/dataspace-signing
```

Look for `deletion_allowed: true` (should be `false`) or `min_encryption_version` > current version (key may be unusable). If the key is missing, contact infra-lead immediately — this is a critical data integrity issue.

### Step 4: Check Vault policy

```bash
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault policy read dataspace-signer
```

Expected output should include `path "transit/sign/dataspace-signing" { capabilities = ["create", "update"] }`. If this path is missing or has only `read`, the policy has been modified incorrectly. See Scenario C.

### Step 5: Check Vault audit log for recent errors

```bash
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault audit list

# If file audit is enabled, check recent entries
kubectl exec -it vault-0 -n dataspace-infra -- \
  tail -20 /vault/audit/audit.log | python3 -m json.tool | grep -E '"error"|"type"'
```

## Remediation / Rollback

!!! danger "Unseal key holders only"
    Vault unsealing requires the participation of at least 3 of the 5 unseal key holders. Unseal keys are distributed across 3 individuals via PGP-encrypted secure channel. Never store unseal keys on the cluster or in any automated system.

### Scenario A: Vault is sealed

Vault seals automatically when: it restarts (auto-unseal is not configured in dev), when the storage backend becomes unavailable, or when a quorum of Vault nodes is lost.

**If auto-unseal is configured (production)**: Vault should unseal automatically when the pod restarts. Check if the KMS key (AWS KMS / GCP Cloud KMS) is accessible.

```bash
# Restart the Vault pod — it should auto-unseal
kubectl rollout restart statefulset/vault -n dataspace-infra
kubectl rollout status statefulset/vault -n dataspace-infra

# After restart, verify unsealed
kubectl exec -it vault-0 -n dataspace-infra -- vault status
```

**If manual unseal is required (dev / auto-unseal misconfigured)**: Contact the 3 unseal key holders via secure out-of-band channel. Each holder must provide their shard via:

```bash
# Each key holder runs this on their terminal (never send shards via Slack or email)
kubectl exec -it vault-0 -n dataspace-infra -- vault operator unseal
# Enter the shard when prompted
```

Repeat with 3 different key holders' shards. After the third shard, Vault unseals.

**Verify**: `kubectl exec -it vault-0 -n dataspace-infra -- vault status` → `Sealed: false`

### Scenario B: Token expired or revoked

```bash
# Re-authenticate via Vault AppRole (secrets stored in Kubernetes Secret)
APP_ROLE_ID=$(kubectl get secret vault-approle -n dataspace-platform -o jsonpath='{.data.role-id}' | base64 -d)
SECRET_ID=$(kubectl get secret vault-approle -n dataspace-platform -o jsonpath='{.data.secret-id}' | base64 -d)

kubectl exec -it vault-0 -n dataspace-infra -- \
  vault write auth/approle/login role_id="${APP_ROLE_ID}" secret_id="${SECRET_ID}"

# Store the new token back in the secret
NEW_TOKEN="<token from vault write output>"
kubectl patch secret vault-approle -n dataspace-platform \
  --type=json \
  -p='[{"op":"replace","path":"/data/vault-token","value":"'$(echo -n "${NEW_TOKEN}" | base64)'"}]'

# Restart temporal-workers to pick up the new token
kubectl rollout restart deployment/temporal-workers -n dataspace-platform
```

### Scenario C: Policy revoked or incorrect

```bash
# Restore the dataspace-signer policy from Terraform state
cd infra/terraform/roots/platform
terraform plan -target=vault_policy.dataspace_signer
terraform apply -target=vault_policy.dataspace_signer
```

Or manually restore:

```bash
kubectl exec -it vault-0 -n dataspace-infra -- vault policy write dataspace-signer - <<'EOF'
path "transit/sign/dataspace-signing" {
  capabilities = ["create", "update"]
}
path "transit/verify/dataspace-signing" {
  capabilities = ["create", "update"]
}
path "transit/sign/dataspace-signing/*" {
  capabilities = ["create", "update"]
}
EOF
```

## Evidence Capture Requirements

- [ ] `vault status` output at time of alert
- [ ] Vault audit log entries from the 30 minutes before the alert (if audit logging was enabled)
- [ ] Temporal worker logs showing signing errors: `kubectl logs deployment/temporal-workers -n dataspace-platform --since=1h | grep -i vault`
- [ ] List of workflows that failed permanently (entered FAILED state) vs those that retried successfully

## Dashboards / Logs / Traces

| Resource | URL |
|---------|-----|
| Grafana — Vault Dashboard | `https://grafana.your-org.internal/d/vault-overview` |
| Vault UI | `https://vault.your-org.internal` |
| Loki — temporal-workers vault errors | `{namespace="dataspace-platform", app="temporal-workers"} \|= "vault" \| json \| level="ERROR"` |
| Temporal UI — stalled workflows | `https://temporal.your-org.internal/namespaces/dataspace/workflows?status=Running` |

## Escalation Contacts

| Role | Contact | Escalation trigger |
|------|---------|-------------------|
| infra-lead | `@infra-lead` PagerDuty | Not resolved in 10 min |
| Unseal key holders | Via secure channel (see key holder list in 1Password) | Vault needs manual unseal |
| Platform lead | `@platform-lead` Slack | Not resolved in 30 min; key is missing or corrupted |

## Post-Incident Follow-Up

- [ ] Verify all stalled Temporal workflows resumed successfully after Vault recovery
- [ ] Audit which signing operations were missed during the outage window
- [ ] Review whether auto-unseal (KMS) was correctly configured and why it did not prevent sealing
- [ ] Update `docs/arc42/11-risks-and-technical-debt.md` Risk R-06 status if a Vault HA gap was identified

## Related Runbooks

- [Vault Key Rotation](../platform/vault-key-rotation.md) — if key version issues caused the failures
- [Temporal Workers Stalled](temporal-workers-stalled.md) — Vault failures cause worker activity stalls
- [Certificate Renewal](../platform/certificate-renewal.md) — if Vault PKI certificates expired
