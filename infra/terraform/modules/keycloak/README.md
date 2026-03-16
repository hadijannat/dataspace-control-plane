# Module: keycloak

Provider-neutral identity contract with two modes:

- `dev-scaffold`: deploy Keycloak in Kubernetes for local development
- `external`: reference a shared Keycloak service and its externally managed URLs

## Notes

- The in-cluster deployment is suitable for development scaffolding only.
- Shared environments should keep Keycloak lifecycle outside this repo until a provider-specific implementation is chosen.
- This module exposes URLs and service names, not administrator secrets.

## Key Inputs

| Name | Description |
|------|-------------|
| `mode` | `dev-scaffold` or `external` |
| `namespace` | Kubernetes namespace |
| `realm_name` | Default realm name |
| `admin_secret_name` | Existing Secret name for admin credentials in scaffold mode |
| `external_service_name` | Shared Keycloak service label or reference name |
| `external_admin_url` | External admin URL |
| `external_realm_url` | External realm URL |

## Outputs

| Name | Description |
|------|-------------|
| `service_name` | In-cluster or external service reference |
| `admin_url` | In-cluster or external admin URL |
| `realm_url` | In-cluster or external realm URL |
