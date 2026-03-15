# Module: postgres

Deploys a PostgreSQL instance. The default implementation creates a single-node Postgres Deployment in Kubernetes, suitable for dev/CI. **Not for production data durability.**

Before production deployment, replace `kubernetes_deployment.postgres` and `kubernetes_persistent_volume_claim.postgres_data` with a managed database resource:

- **Google Cloud SQL**: `google_sql_database_instance` + `google_sql_database` + `google_sql_user`
- **AWS RDS**: `aws_db_instance`
- **Azure Database for PostgreSQL Flexible Server**: `azurerm_postgresql_flexible_server`
- **CloudNativePG operator**: Use a `Cluster` CRD via `kubectl_manifest`

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `instance_name` | string | — | yes | Name prefix for all resources |
| `namespace` | string | — | yes | K8s namespace |
| `database_name` | string | — | yes | Default database name |
| `username` | string | — | yes | Postgres username |
| `storage_size` | string | `"10Gi"` | no | PVC size |
| `version` | string | `"16"` | no | Postgres major version |
| `backup_enabled` | bool | `true` | no | Enable backups (managed service feature) |
| `labels` | map(string) | `{}` | no | Resource labels |

## Outputs

| Name | Description |
|------|-------------|
| `host` | In-cluster hostname |
| `port` | Port (5432) |
| `database_name` | Database name |
| `secret_name` | K8s Secret name for Helm values |
