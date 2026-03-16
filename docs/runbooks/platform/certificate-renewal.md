---
title: "Certificate Renewal"
summary: "Procedure for renewing TLS certificates managed by Vault PKI, with steps for both cert-manager auto-renewal and manual renewal when automation fails."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P2"
affected_services:
  - control-api
  - temporal-workers
  - provisioning-agent
  - keycloak
status: approved
---

## When to Run This Procedure

Normally, cert-manager handles certificate renewal automatically (renews 30 days before expiry). Run this manual procedure when:

- cert-manager auto-renewal has failed (alert: `CertificateExpiringSoon` AND cert-manager not issuing)
- A certificate has been compromised and must be revoked and replaced immediately
- A root CA certificate is expiring and the entire PKI chain needs renewal

## Pre-Checks

```bash
# List all certificates managed by cert-manager
kubectl get certificates -n dataspace-platform
kubectl get certificates -n dataspace-infra

# Check certificate expiry
kubectl get certificates -n dataspace-platform -o jsonpath='{range .items[*]}{.metadata.name}{" expires: "}{.status.notAfter}{"\n"}{end}'

# Check cert-manager controller logs for errors
kubectl logs deployment/cert-manager -n cert-manager --tail=50 | grep -E "ERROR|error|certificate"

# Check Vault PKI engine health
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault pki health-check dataspace-pki/
```

## Procedure: Renew a Single Certificate via cert-manager

If cert-manager is functional but has not renewed a specific certificate:

```bash
# Delete the existing TLS Secret to force cert-manager to re-issue
# (cert-manager watches the Secret and will create a new one immediately)
kubectl delete secret control-api-tls -n dataspace-platform

# Watch cert-manager issue the new certificate
kubectl get certificate control-api-cert -n dataspace-platform -w

# Expected: READY=True within 60 seconds
```

## Procedure: Manual Certificate Issuance via Vault PKI

When cert-manager is unavailable or misconfigured:

### Step 1: Check certificate expiry dates

```bash
# List all issued certificates in Vault PKI
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault list dataspace-pki/certs

# Check a specific certificate's expiry
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault read dataspace-pki/cert/<serial-number>
```

### Step 2: Issue a new certificate

```bash
# Issue a new certificate for control-api
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault write dataspace-pki/issue/platform-services \
    common_name="control-api.dataspace-platform.svc.cluster.local" \
    alt_names="api.your-org.internal" \
    ttl="720h" \
    > /tmp/new-cert.json

# Extract certificate and private key from the response
cat /tmp/new-cert.json | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['certificate'])" > /tmp/tls.crt
cat /tmp/new-cert.json | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['private_key'])" > /tmp/tls.key
```

### Step 3: Update the Kubernetes TLS Secret

```bash
# Update the Kubernetes Secret with the new certificate
kubectl create secret tls control-api-tls \
  -n dataspace-platform \
  --cert=/tmp/tls.crt \
  --key=/tmp/tls.key \
  --dry-run=client -o yaml | kubectl apply -f -

# Remove the temporary files immediately
rm -f /tmp/new-cert.json /tmp/tls.crt /tmp/tls.key
```

!!! danger "Handle private key files with care"
    The `/tmp/tls.key` file contains a private key. Remove it immediately after updating the Kubernetes Secret. Do not log the contents or store it in any persistent location.

### Step 4: Restart affected pods

```bash
# Restart to pick up the new certificate from the Secret
kubectl rollout restart deployment/control-api -n dataspace-platform
kubectl rollout status deployment/control-api -n dataspace-platform
```

### Step 5: Verify TLS handshake

```bash
# Verify the new certificate is served
openssl s_client -connect api.your-org.internal:443 -servername api.your-org.internal < /dev/null 2>/dev/null | \
  openssl x509 -noout -dates -subject

# Expected: notAfter should be 30 days from now
```

### Step 6: Revoke the old certificate

```bash
# Revoke the old certificate using its serial number (from the old Secret or cert output)
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault write dataspace-pki/revoke \
    serial_number="<OLD_SERIAL_NUMBER>"
```

## Root CA Renewal (High-Impact — Requires Coordination)

Root CA renewal affects all certificates in the PKI chain and requires coordination with all service owners. Do not proceed without:

- infra-lead approval
- Scheduled maintenance window
- Rollback plan (keep old CA certificate in trust bundle during transition)

Contact infra-lead before attempting root CA renewal.

## Evidence Capture Requirements

- [ ] Pre-renewal certificate subject and expiry date
- [ ] Post-renewal certificate subject and expiry date
- [ ] Serial number of revoked certificate (if applicable)
- [ ] `openssl s_client` output confirming new certificate is served

## Related Runbooks

- [Vault Key Rotation](vault-key-rotation.md) — if signing keys also need rotation
- [Vault Transit Failures](../incidents/vault-transit-failures.md) — if Vault PKI engine was unavailable
