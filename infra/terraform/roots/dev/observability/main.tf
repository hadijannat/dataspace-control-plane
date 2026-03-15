# dev/observability — Deploys kube-prometheus-stack with Grafana.
# Loki and Tempo disabled in dev to minimize resource usage.

module "observability" {
  source = "../../../modules/observability"

  namespace               = var.namespace
  prometheus_storage_size = "20Gi"
  grafana_enabled         = true
  loki_enabled            = false
  tempo_enabled           = false
  labels = {
    "environment" = "dev"
  }
}
