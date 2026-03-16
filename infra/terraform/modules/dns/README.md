# Module: dns

Provider-neutral DNS contract.

This module currently models shared DNS state by reference. It does not create zones or records until a concrete provider choice is made.

## Notes

- Use `mode = "external"` for shared environments.
- Keep zone identifiers and desired record metadata in Terraform.
- Keep provider credentials out of the repo and avoid pretending placeholder resources are real DNS automation.

## Key Inputs

| Name | Description |
|------|-------------|
| `mode` | Expected to be `external` in current roots |
| `zone_name` | DNS zone name |
| `records` | Desired DNS record metadata |
| `external_zone_id` | Existing shared zone identifier |

## Outputs

| Name | Description |
|------|-------------|
| `zone_id` | Shared zone identifier |
| `zone_name` | Zone name |
