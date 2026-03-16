# prod-eu/observability — Full stack: Prometheus 200Gi, Grafana, Loki, Tempo.

module "observability" {
  source = "../../../modules/observability"

  namespace               = var.namespace
  prometheus_storage_size = "200Gi"
  grafana_enabled         = true
  grafana_admin_secret_name = var.grafana_admin_secret_name
  loki_enabled            = true
  tempo_enabled           = true
  labels = {
    "environment" = "prod-eu"
    "region"      = "eu"
  }
}
