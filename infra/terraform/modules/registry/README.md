# Module: registry

Provider-neutral registry contract with two modes:

- `dev-scaffold`: record a local registry contract in-cluster
- `external`: reference a shared registry URL without creating the registry itself

## Notes

- The dev scaffold path is intentionally lightweight. It creates a ConfigMap that documents the registry contract for local stacks.
- Shared environments must use `mode = "external"` and provide a real registry URL.
- Choosing and provisioning Harbor, ECR, GAR, ACR, or another registry remains a separate provider decision.

## Key Inputs

| Name | Description |
|------|-------------|
| `mode` | `dev-scaffold` or `external` |
| `name` | Registry or repository name |
| `namespace` | Namespace for scaffold metadata |
| `storage_limit_gb` | Capacity hint for scaffold metadata |
| `external_registry_url` | Shared registry URL when `mode = "external"` |

## Outputs

| Name | Description |
|------|-------------|
| `registry_url` | Scaffold or external registry URL |
| `registry_name` | Registry name |
