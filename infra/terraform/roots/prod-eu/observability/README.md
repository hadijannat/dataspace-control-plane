# prod-eu/observability

Full observability stack for production EU. Prometheus 200Gi, Grafana, Loki (logs), Tempo (traces).

```bash
cd infra/terraform/roots/prod-eu/observability
terraform init -backend-config=../../../backends/prod-eu.backend.hcl
terraform plan -out=prod-eu-obs.tfplan
terraform apply prod-eu-obs.tfplan
```
