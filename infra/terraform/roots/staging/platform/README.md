# staging/platform

Platform root for staging. Deploys Postgres (20Gi), Keycloak, Vault, ingress (2 replicas).

```bash
cd infra/terraform/roots/staging/platform
terraform init -backend-config=../../../backends/staging.backend.hcl
terraform apply
```
