# Module: keycloak

Deploys Keycloak identity server in Kubernetes (dev/staging) or configures a managed identity service (production).

For production, replace the Kubernetes resources with the Keycloak Terraform provider (`mrparkers/keycloak`) to configure realms, clients, and identity providers declaratively.

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `namespace` | string | — | yes | K8s namespace |
| `realm_name` | string | — | yes | Default realm name |
| `admin_secret_name` | string | — | yes | K8s Secret name with admin credentials |
| `storage_size` | string | `"5Gi"` | no | PVC size |
| `labels` | map(string) | `{}` | no | Resource labels |

## Outputs

| Name | Description |
|------|-------------|
| `service_name` | Keycloak service name |
| `admin_url` | Admin console URL (in-cluster) |
| `realm_url` | Realm discovery URL (in-cluster) |
