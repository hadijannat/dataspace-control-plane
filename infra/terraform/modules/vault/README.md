# Module: vault

Deploys HashiCorp Vault in Kubernetes. Dev mode for local environments; for production, use the official Vault Helm chart with auto-unseal.

## Security Warning

This module runs Vault in dev mode (`vault server -dev`) for development environments. **Dev mode is not suitable for production** — it stores everything in memory, auto-unseals, and exposes a root token.

For production:
1. Use the official `hashicorp/vault` Helm chart with `ha.enabled=true` and Raft storage
2. Configure auto-unseal with cloud KMS (AWS KMS, GCP Cloud KMS, Azure Key Vault)
3. Use the `hashicorp/vault` Terraform provider to manage engines, policies, and auth methods

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `namespace` | string | — | yes | K8s namespace |
| `storage_size` | string | `"10Gi"` | no | PVC size |
| `ha_enabled` | bool | `false` | no | Enable HA (3 replicas) |
| `transit_enabled` | bool | `true` | no | Enable Transit secrets engine |
| `pki_enabled` | bool | `true` | no | Enable PKI secrets engine |
| `labels` | map(string) | `{}` | no | Resource labels |

## Outputs

| Name | Description |
|------|-------------|
| `vault_addr` | In-cluster Vault API address |
| `service_name` | Vault service name |
| `root_token_secret_name` | Name of the root token K8s Secret (dev only) |
