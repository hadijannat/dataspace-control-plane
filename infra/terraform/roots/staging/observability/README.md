# staging/observability

Deploys the shared staging monitoring stack with Prometheus, Grafana, and Loki.

Provide `grafana_admin_secret_name` through `terraform.tfvars` or rely on the default example value if it matches the environment.

```bash
cd infra/terraform/roots/staging/observability
terraform init -backend-config=../../../backends/staging.backend.hcl
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
