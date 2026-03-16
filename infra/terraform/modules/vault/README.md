# Module: vault

Provider-neutral secret-store contract with two modes:

- `dev-scaffold`: deploy Vault in development mode inside Kubernetes
- `external`: reference a shared Vault address and service name

## Notes

- `dev-scaffold` runs Vault in dev mode and is for local work only.
- Shared environments should use `mode = "external"` until a production-grade Vault implementation is selected.
- Transit and PKI enablement remain scaffold conveniences; shared environments should manage those concerns in the real Vault control plane.

## Key Inputs

| Name | Description |
|------|-------------|
| `mode` | `dev-scaffold` or `external` |
| `namespace` | Kubernetes namespace |
| `ha_enabled` | Development scaffold replica count control |
| `transit_enabled` | Enable transit in scaffold mode |
| `pki_enabled` | Enable PKI in scaffold mode |
| `external_vault_addr` | Shared Vault API address |
| `external_service_name` | Shared Vault service reference |
| `external_root_token_secret_name` | Optional existing secret name for development-oriented token handling |

## Outputs

| Name | Description |
|------|-------------|
| `vault_addr` | In-cluster or external Vault address |
| `service_name` | In-cluster or external service reference |
| `root_token_secret_name` | Scaffold token secret or external reference |
