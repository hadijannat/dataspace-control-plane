# Module: registry

Generic container registry module. The placeholder implementation creates a Kubernetes ConfigMap documenting the registry config.

**Before use**: Replace the `kubernetes_config_map` resource in `main.tf` with your registry provider resource. Options:
- Harbor: `harbor_project` (provider: `goharbor/harbor`)
- AWS ECR: `aws_ecr_repository` (provider: `hashicorp/aws`)
- GCP Artifact Registry: `google_artifact_registry_repository` (provider: `hashicorp/google`)
- Azure ACR: `azurerm_container_registry` (provider: `hashicorp/azurerm`)

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `name` | string | — | yes | Registry project/repository name |
| `namespace` | string | — | yes | K8s namespace for ConfigMap |
| `storage_limit_gb` | number | `50` | no | Storage limit in GB |
| `labels` | map(string) | `{}` | no | Resource labels |

## Outputs

| Name | Description |
|------|-------------|
| `registry_url` | Registry URL (update after provider substitution) |
| `registry_name` | Registry name |
