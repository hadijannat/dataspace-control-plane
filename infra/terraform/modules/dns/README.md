# Module: dns

Provider-agnostic DNS zone and record management. Replace the placeholder with your DNS provider resource.

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `zone_name` | string | — | yes | DNS zone name |
| `records` | list(object) | `[]` | no | DNS records to create |

## Outputs

| Name | Description |
|------|-------------|
| `zone_id` | DNS zone ID |
| `zone_name` | DNS zone name |
