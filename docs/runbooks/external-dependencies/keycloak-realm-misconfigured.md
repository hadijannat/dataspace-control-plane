---
title: "Keycloak Realm Misconfigured"
summary: "Runbook for diagnosing and recovering from Keycloak realm misconfiguration causing 401 errors or operator login failures."
owner: infra-lead
last_reviewed: "2026-03-14"
severity: "P2"
affected_services:
  - control-api
  - web-console
  - temporal-workers
  - provisioning-agent
status: approved
---

# Keycloak Realm Misconfigured

## Trigger / Alert Source

- **Alert names**: `KeycloakAuthFailureRateHigh`, `OperatorLoginFailure`
- **Alert conditions**: `rate(keycloak_login_attempts_total{result="error"}[5m]) > 0.5` OR control-api `401` response rate > 10%
- **Manual trigger**: Operator reports they cannot log into the web-console; machine service reports `401 Unauthorized` on all API calls; `curl` to the OIDC configuration endpoint returns error
- **Typical symptom**: Grafana shows a spike in 401 responses from control-api; web-console login redirects to Keycloak but returns "Invalid client" or "Realm not found" error

## Scope and Blast Radius

**Affected when Keycloak realm is misconfigured:**

- **All API calls**: control-api rejects all requests with `401 Unauthorized` (cannot verify JWT without JWKS endpoint)
- **web-console**: Login flow broken — operators cannot authenticate
- **temporal-workers**: Service accounts cannot obtain tokens → signing and DB activities that require authentication fail
- **provisioning-agent**: Cannot perform admin operations requiring Keycloak Admin REST credentials

**NOT affected:**

- **Postgres**: Data is intact; independent of Keycloak
- **Vault**: Independent of Keycloak (uses AppRole auth, not OIDC)
- **Temporal Server**: Workflow history and scheduling are independent
- **BaSyx AAS Server**: If not using Keycloak for auth, unaffected

**Data loss risk**: None — Keycloak misconfiguration is a configuration issue, not a data issue.

## Pre-Checks

```bash
# Check if Keycloak pod is running
kubectl get pods -n dataspace-infra | grep keycloak

# Test the OIDC discovery endpoint for a specific tenant realm
REALM="tenant-BPNL000000000001"
curl -sk https://keycloak.dataspace-infra.svc.cluster.local:8080/realms/${REALM}/.well-known/openid-configuration | python3 -m json.tool

# Check Keycloak pod logs for errors
kubectl logs deployment/keycloak -n dataspace-infra --tail=100 | grep -E "ERROR|error|realm|client"
```

## Triage Checklist

1. [ ] Is the Keycloak pod running and ready?
2. [ ] Does the OIDC discovery endpoint for the affected realm return a valid JSON response?
3. [ ] Does the realm exist in Keycloak? (Check Keycloak admin console)
4. [ ] Is the `control-api` client configured correctly in the realm? (redirect URIs, client type, PKCE settings)
5. [ ] Has a recent Terraform apply or manual change been made to the Keycloak realm?
6. [ ] Is this affecting one specific tenant's realm or all realms?

## Investigation Steps

### Step 1: Test the OIDC configuration endpoint

```bash
# Replace REALM with the affected tenant realm name
REALM="tenant-BPNL000000000001"
KEYCLOAK_URL="https://keycloak.dataspace-infra.svc.cluster.local:8080"

curl -sk "${KEYCLOAK_URL}/realms/${REALM}/.well-known/openid-configuration"
```

**If response is `{"error": "Realm does not exist"}`**: The realm was deleted or never created. See Scenario A.
**If response is a valid JSON object with `jwks_uri`, `token_endpoint`, etc.**: Realm exists. Proceed to Step 2.

### Step 2: Test token issuance with a test client

```bash
# Attempt to obtain a client_credentials token
CLIENT_ID="provisioning-agent"
CLIENT_SECRET="<secret from Vault>"

curl -sk -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" \
  "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token"
```

**If `invalid_client`**: The `provisioning-agent` client is not configured in this realm. See Scenario B.
**If `unauthorized_client`**: The client exists but `client_credentials` grant is not enabled. See Scenario C.
**If valid token returned**: Token issuance works — the issue may be in JWT validation at control-api. See Scenario D.

### Step 3: Check control-api JWT validation configuration

```bash
# Check the KEYCLOAK_JWKS_URL environment variable in control-api
kubectl exec -it deployment/control-api -n dataspace-platform -- \
  env | grep KEYCLOAK

# Test that the JWKS endpoint is reachable from control-api
kubectl exec -it deployment/control-api -n dataspace-platform -- \
  curl -sk "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/certs" | python3 -m json.tool | grep kid
```

**If no `kid` values returned**: JWKS endpoint is misconfigured or unreachable from the control-api pod.

## Remediation

### Scenario A: Realm deleted or does not exist

The realm needs to be recreated. The authoritative realm configuration is in Terraform:

```bash
cd infra/terraform/roots/platform
terraform plan -target=keycloak_realm.tenant_realms
terraform apply -target=keycloak_realm.tenant_realms
```

If only one tenant's realm is missing and the company ID is known, re-run the onboarding workflow via the API:

```bash
# The OnboardingWorkflow CreateRealm activity will re-create the realm
curl -X POST https://api.your-org.internal/api/v1/companies \
  -H "Authorization: Bearer <admin-token>" \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{"legalEntityId": "<BPNL>", "displayName": "<name>"}'
```

### Scenario B: Client not configured in realm

The `control-api` or `provisioning-agent` client is missing from the realm. Restore from Terraform:

```bash
cd infra/terraform/roots/platform
terraform plan -target=keycloak_openid_client.control_api
terraform apply -target=keycloak_openid_client.control_api
```

Or manually in the Keycloak admin console:

1. Navigate to: `https://keycloak.your-org.internal/admin` → Select realm → Clients → Create
2. Client ID: `control-api`
3. Client Protocol: `openid-connect`
4. Access Type: `confidential` (for service accounts) or `public` (for web-console)
5. Enable `Service Accounts Enabled` for machine clients
6. Set correct redirect URIs: `https://console.your-org.internal/*`

### Scenario C: client_credentials grant not enabled

In Keycloak admin console: Clients → `provisioning-agent` → Settings → `Service Accounts Enabled: ON`

Or via Terraform:
```bash
terraform plan -target=keycloak_openid_client.provisioning_agent
terraform apply -target=keycloak_openid_client.provisioning_agent
```

### Scenario D: JWKS cache stale in control-api

If the realm's signing keys were rotated (e.g., Keycloak realm re-import), control-api's JWKS cache may be serving old public keys:

```bash
# Restart control-api to clear the JWKS cache
kubectl rollout restart deployment/control-api -n dataspace-platform
kubectl rollout status deployment/control-api -n dataspace-platform
```

## Evidence Capture Requirements

- [ ] OIDC discovery endpoint response for the affected realm
- [ ] Keycloak admin console screenshot of the client configuration
- [ ] control-api logs showing the JWT validation error
- [ ] Terraform plan output showing what was applied to fix the configuration

## Escalation Contacts

| Role | Contact | Escalation trigger |
|------|---------|-------------------|
| infra-lead | `@infra-lead` Slack / PagerDuty | Not resolved in 10 min |
| Platform lead | `@platform-lead` Slack | Not resolved in 30 min; realm data at risk |

## Post-Incident Follow-Up

- [ ] Identify what caused the realm misconfiguration (manual change, Terraform drift, deployment bug)
- [ ] Update the Keycloak Terraform module to prevent recurrence
- [ ] Review whether realm configuration should be protected by a Terraform state lock

## Related Runbooks

- [Vault Transit Failures](../incidents/vault-transit-failures.md) — Vault unavailability can cause provisioning-agent to fail on client_secret retrieval
- [Connector Registration Failed](../procedures/connector-registration-failed.md) — often caused by Keycloak credential issues
