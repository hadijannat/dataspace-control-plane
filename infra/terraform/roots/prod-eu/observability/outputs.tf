output "prometheus_endpoint" {
  value = module.observability.prometheus_endpoint
}

output "grafana_service_name" {
  value = module.observability.grafana_service_name
}

output "alertmanager_endpoint" {
  value = module.observability.alertmanager_endpoint
}
