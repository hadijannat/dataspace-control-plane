# staging/observability

Observability root for staging. Deploys kube-prometheus-stack (50Gi) with Grafana and Loki.

```bash
cd infra/terraform/roots/staging/observability
terraform init -backend-config=../../../backends/staging.backend.hcl
terraform apply
```
