# Module: postgres

Provider-neutral Postgres contract with two modes:

- `dev-scaffold`: deploy a single-node Postgres instance in Kubernetes for local development
- `external`: reference a durable shared Postgres service by host, port, and secret name

## Notes

- The Kubernetes deployment path is for local development only. It is not a production durability story.
- Shared environments should use `mode = "external"` and inject credentials through an existing Kubernetes Secret or external secret workflow.
- Secret bodies are intentionally not modeled for shared environments.

## Key Inputs

| Name | Description |
|------|-------------|
| `mode` | `dev-scaffold` or `external` |
| `instance_name` | Resource name prefix |
| `namespace` | Kubernetes namespace |
| `database_name` | Logical database name |
| `username` | Database username |
| `external_host` | Shared Postgres hostname when `mode = "external"` |
| `external_port` | Shared Postgres port when `mode = "external"` |
| `external_secret_name` | Existing Secret name referenced by workloads when `mode = "external"` |

## Outputs

| Name | Description |
|------|-------------|
| `host` | In-cluster or external hostname |
| `port` | In-cluster or external port |
| `database_name` | Database name |
| `secret_name` | Secret reference for downstream workloads |
