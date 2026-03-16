---
title: "Connector Registration Failed"
summary: "Runbook for diagnosing and recovering from EDC connector registration failures in the provisioning-agent."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P2"
affected_services:
  - provisioning-agent
  - apps/edc-extension
status: approved
---

## Trigger / Alert Source

- **Alert names**: `ConnectorRegistrationFailed`, `ProvisioningAgentError`
- **Alert conditions**: `connector_registration_failed_total` counter incrementing, OR provisioning-agent logs showing repeated registration attempt failures
- **Manual trigger**: Operator reports that a newly onboarded company's EDC connector is not visible in the Catena-X dataspace catalog; or operator reports `status: failed` on a company that completed Keycloak provisioning but failed at connector registration
- **Typical symptom**: Company record in Postgres has `status: provisioning` and the OnboardingWorkflow Temporal history shows failure at the `register_edc_connector` activity

## Scope and Blast Radius

**Affected:**

- **provisioning-agent**: Cannot register the connector for the affected company. Other companies' registrations are unaffected (one-per-tenant isolation).
- **Catena-X dataspace participation**: The company cannot publish catalog entries or participate in contract negotiations until the connector is registered.

**NOT affected:**

- **Keycloak realm**: Already provisioned — authentication still works.
- **Vault signing keys**: Already provisioned — signing still works for other operations.
- **Other tenant operations**: Fully isolated; not impacted.

**Data loss risk**: None — registration is idempotent. Re-running the workflow creates or updates the connector registration.

## Pre-Checks

```bash
# Check provisioning-agent pod status
kubectl get pods -n dataspace-platform | grep provisioning-agent

# Check provisioning-agent logs
kubectl logs deployment/provisioning-agent -n dataspace-platform --tail=100 | grep -E "ERROR|registration|connector"

# Check which company's registration failed (from Temporal UI or Postgres)
kubectl exec -it postgres-0 -n dataspace-infra -- \
  psql -U dataspace -c "SELECT company_id, status, legal_entity_id FROM companies WHERE status='provisioning' ORDER BY created_at DESC LIMIT 10;"
```

## Triage Checklist

1. [ ] Is the provisioning-agent pod running?
2. [ ] Is the EDC connector pod for this tenant reachable? (`kubectl get pods -n <tenant-namespace>`)
3. [ ] Is the EDC connector's DSP catalog endpoint reachable from the provisioning-agent?
4. [ ] Are the Keycloak client credentials for the provisioning-agent valid?
5. [ ] Was the EDC connector deployed before the registration was attempted?

## Investigation Steps

### Step 1: Find the failed workflow in Temporal UI

Navigate to `https://temporal.your-org.internal` → Namespace: `dataspace` → filter by workflow type `OnboardingWorkflow` and status `Failed` or `Running`. Click the workflow for the affected `company_id`.

Look at the workflow event history for the last activity before failure. Common failure points:

- `create_keycloak_realm` → Keycloak issue (see [Keycloak Realm Misconfigured](../external-dependencies/keycloak-realm-misconfigured.md))
- `register_edc_connector` → connector or provisioning-agent issue (this runbook)
- `sign_did_document` → Vault issue (see [Vault Transit Failures](../incidents/vault-transit-failures.md))

### Step 2: Test DSP endpoint reachability

```bash
# From within the provisioning-agent pod:
kubectl exec -it deployment/provisioning-agent -n dataspace-platform -- \
  curl -sk https://edc-connector.<tenant-namespace>.svc.cluster.local:8080/api/v1/dsp/catalog/request \
  -H "Content-Type: application/json" \
  -d '{"@context": {"edc": "https://w3id.org/edc/v0.0.1/ns/"}, "@type": "edc:CatalogRequest"}'
```

**If connection refused**: The EDC connector pod is not running or not reachable. Check:

```bash
kubectl get pods -n <tenant-namespace>
kubectl logs deployment/edc-connector -n <tenant-namespace> --tail=50
```

**If 401 Unauthorized**: The provisioning-agent's Keycloak credentials for this tenant are incorrect. See Step 3.

### Step 3: Verify provisioning-agent Keycloak credentials

```bash
# Check the credentials stored in Vault
kubectl exec -it vault-0 -n dataspace-infra -- \
  vault kv get secret/platform/provisioning-agent/<tenant-id>/keycloak-client-secret

# Test authentication
kubectl exec -it deployment/provisioning-agent -n dataspace-platform -- \
  curl -sk -d "grant_type=client_credentials&client_id=provisioning-agent&client_secret=<secret>" \
  https://keycloak.dataspace-infra.svc.cluster.local:8080/realms/<tenant-realm>/protocol/openid-connect/token
```

If this fails with 401: the client secret is wrong or the client is not configured in Keycloak. Re-run the Keycloak client creation step via the workflow re-submission.

## Remediation

### Scenario A: EDC connector pod not running

Deploy or restart the EDC connector for the affected tenant:

```bash
kubectl rollout restart deployment/edc-connector -n <tenant-namespace>
kubectl rollout status deployment/edc-connector -n <tenant-namespace>
```

Then re-submit the registration:

```bash
# Re-submit via control-api (idempotent — uses the same idempotency key as the original)
curl -X POST https://api.your-org.internal/api/v1/companies \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: <original-idempotency-key>" \
  -H "Content-Type: application/json" \
  -d '{"legalEntityId": "<BPNL>", "displayName": "<name>"}'
```

### Scenario B: Connector reachable but registration rejected

Check EDC connector logs for the rejection reason:

```bash
kubectl logs deployment/edc-connector -n <tenant-namespace> --tail=100 | grep -E "ERROR|registration|rejected"
```

Common causes: missing required DID in management API call, wrong connector ID format, or missing trust credential. Fix the connector configuration and re-submit.

## Evidence Capture Requirements

- [ ] Temporal workflow history for the failed OnboardingWorkflow (screenshot or export)
- [ ] provisioning-agent logs from the failure window
- [ ] EDC connector logs if connector was unreachable

## Related Runbooks

- [Keycloak Realm Misconfigured](../external-dependencies/keycloak-realm-misconfigured.md) — if Keycloak credentials failed
- [Vault Transit Failures](../incidents/vault-transit-failures.md) — if signing step failed before registration
- [Temporal Workers Stalled](../incidents/temporal-workers-stalled.md) — if workers are not processing activities
