# control-api Helm Chart

Deploys the `control-api` FastAPI service for the dataspace control plane.

## What This Chart Deploys

- **Deployment** — control-api pods with security hardening (non-root, readOnlyRootFilesystem, capabilities dropped)
- **Service** — ClusterIP service exposing port 80 → 8080
- **ServiceAccount** — dedicated service account (RBAC-ready)
- **ConfigMap** — non-secret configuration (log level, OTEL endpoint, Temporal coordinates)
- **Ingress** — optional, disabled by default; enable via `ingress.enabled=true`
- **HPA** — optional horizontal pod autoscaler; enable via `autoscaling.enabled=true`

## Required Secrets

The chart references K8s Secret names. These Secrets must exist in the namespace before installing the chart. Use ExternalSecret (ESO), SealedSecret, or Vault CSI to create them.

| Values key | Secret name (default) | Required keys |
|-----------|----------------------|--------------|
| `secrets.postgresSecretName` | `control-api-postgres` | `DATABASE_URL` |
| `secrets.vaultSecretName` | `control-api-vault` | `VAULT_ADDR`, `VAULT_TOKEN` |
| `secrets.keycloakSecretName` | `control-api-keycloak` | `KEYCLOAK_URL`, `CLIENT_SECRET` |

## Quick Install

```bash
# Dev
helm upgrade --install control-api infra/helm/charts/control-api \
  --namespace dataspace \
  --create-namespace \
  -f infra/helm/values/dev/control-api.yaml

# Production EU
helm upgrade --install control-api infra/helm/charts/control-api \
  --namespace dataspace \
  -f infra/helm/values/prod-eu/control-api.yaml \
  --atomic \
  --timeout 5m
```

## Health Endpoints

The chart configures Kubernetes probes expecting:

- **Liveness**: `GET /health` → 200
- **Readiness**: `GET /health/ready` → 200

The `control-api` application must implement both endpoints.

## Values Reference

See `values.yaml` for full defaults and inline comments.
See `values.schema.json` for validation rules (image tag format, replica bounds, required secrets).
