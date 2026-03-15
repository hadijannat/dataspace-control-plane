# dev/observability

Observability root for the dev environment. Deploys kube-prometheus-stack with Grafana. Loki and Tempo are disabled in dev.

## Usage

```bash
cd infra/terraform/roots/dev/observability
terraform init -backend-config=../../../backends/dev.backend.hcl
terraform apply
```
