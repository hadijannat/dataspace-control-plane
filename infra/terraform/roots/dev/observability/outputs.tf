output "prometheus_endpoint" {
  value       = module.observability.prometheus_endpoint
  description = "Prometheus in-cluster endpoint."
}

output "grafana_service_name" {
  value       = module.observability.grafana_service_name
  description = "Grafana service name."
}
