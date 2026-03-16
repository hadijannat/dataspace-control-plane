# Module: object-storage

Provider-neutral object storage contract.

This module currently models a shared durable dependency by reference. It does not create buckets or storage accounts until a concrete provider choice is made.

## Notes

- Use `mode = "external"` for shared environments.
- Keep bucket URLs, names, and regions in Terraform; keep credentials in external secret systems.
- When a provider is selected, replace this contract with a real implementation rather than hiding a placeholder resource behind the same interface.

## Key Inputs

| Name | Description |
|------|-------------|
| `mode` | Expected to be `external` in current roots |
| `bucket_name` | Logical bucket name |
| `region` | Region or location |
| `versioning_enabled` | Desired versioning policy |
| `external_bucket_url` | Shared object-store URL |

## Outputs

| Name | Description |
|------|-------------|
| `bucket_name` | Bucket name |
| `bucket_url` | Shared bucket URL |
