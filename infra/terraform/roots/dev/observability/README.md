# dev/observability

Deploys the development monitoring stack with Prometheus and Grafana. Loki and Tempo stay disabled to keep the local footprint smaller.

```bash
cd infra/terraform/roots/dev/observability
terraform init -backend-config=../../../backends/dev.backend.hcl
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```
