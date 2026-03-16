# Module: observability

Deploys the shared monitoring stack for a cluster namespace using Helm charts:

- `kube-prometheus-stack`
- optional `loki`
- optional `tempo`

## Notes

- Grafana administrator credentials should come from an existing Kubernetes Secret through `grafana_admin_secret_name`.
- This module owns cluster-adjacent observability components, not application telemetry pipelines. Collector topology remains under `infra/observability/`.
- Loki and Tempo are optional per environment.

## Key Inputs

| Name | Description |
|------|-------------|
| `namespace` | Observability namespace |
| `prometheus_storage_size` | Prometheus PVC size |
| `grafana_enabled` | Enable Grafana |
| `grafana_admin_secret_name` | Existing Secret name for Grafana admin credentials |
| `loki_enabled` | Enable Loki |
| `tempo_enabled` | Enable Tempo |

## Outputs

| Name | Description |
|------|-------------|
| `prometheus_endpoint` | Prometheus in-cluster endpoint |
| `grafana_service_name` | Grafana service name |
| `grafana_admin_secret_name` | Secret reference used for Grafana admin credentials |
| `alertmanager_endpoint` | Alertmanager in-cluster endpoint |
