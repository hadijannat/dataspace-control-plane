# staging/observability — kube-prometheus-stack with Loki enabled for log aggregation.

module "observability" {
  source = "../../../modules/observability"

  namespace               = var.namespace
  prometheus_storage_size = "50Gi"
  grafana_enabled         = true
  loki_enabled            = true
  tempo_enabled           = false
  labels = {
    "environment" = "staging"
  }
}
