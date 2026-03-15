# Module: object-storage

Provider-agnostic object storage bucket module. Replace the placeholder `local_file` resource with your cloud provider's bucket resource.

## Policy Enforcement

OPA policy `infra/terraform/policy/no_public_s3.rego` denies any S3 bucket with `acl = "public-read"`. Apply this policy in CI using `conftest` before applying plans.

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `bucket_name` | string | — | yes | Bucket name (DNS-safe) |
| `region` | string | — | yes | Cloud region |
| `versioning_enabled` | bool | `true` | no | Enable object versioning |
| `labels` | map(string) | `{}` | no | Resource tags |

## Outputs

| Name | Description |
|------|-------------|
| `bucket_name` | Bucket name |
| `bucket_url` | Bucket URL (update after provider substitution) |
