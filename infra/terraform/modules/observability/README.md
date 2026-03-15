# Module: observability

Deploys the Prometheus observability stack using `kube-prometheus-stack` Helm chart, with optional Loki (logs) and Tempo (traces).

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `namespace` | string | — | yes | Observability namespace |
| `prometheus_storage_size` | string | `"50Gi"` | no | Prometheus PVC size |
| `grafana_enabled` | bool | `true` | no | Deploy Grafana |
| `loki_enabled` | bool | `false` | no | Deploy Loki for logs |
| `tempo_enabled` | bool | `false` | no | Deploy Tempo for traces |
| `labels` | map(string) | `{}` | no | Resource labels |

## Outputs

| Name | Description |
|------|-------------|
| `prometheus_endpoint` | Prometheus in-cluster URL |
| `grafana_service_name` | Grafana service name |
| `alertmanager_endpoint` | Alertmanager in-cluster URL |
