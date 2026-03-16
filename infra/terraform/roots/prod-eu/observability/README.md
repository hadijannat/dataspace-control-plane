# prod-eu/observability

Deploys the EU production monitoring stack with Prometheus, Grafana, Loki, and Tempo.

Use an existing Grafana admin secret and apply from a reviewed plan.

```bash
cd infra/terraform/roots/prod-eu/observability
terraform init -backend-config=../../../backends/prod-eu.backend.hcl
terraform plan -out=prod-eu-observability.tfplan -var-file=terraform.tfvars
terraform apply prod-eu-observability.tfplan
```
