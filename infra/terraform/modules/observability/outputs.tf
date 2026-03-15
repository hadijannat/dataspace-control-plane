output "prometheus_endpoint" {
  value       = "http://kube-prometheus-stack-prometheus.${var.namespace}.svc.cluster.local:9090"
  description = "In-cluster Prometheus API endpoint."
}

output "grafana_service_name" {
  value       = var.grafana_enabled ? "kube-prometheus-stack-grafana" : null
  description = "Grafana service name (null when grafana_enabled=false)."
}

output "grafana_admin_secret_name" {
  value       = var.grafana_admin_secret_name
  description = "Existing Grafana admin credentials Secret reference when one is supplied."
}

output "alertmanager_endpoint" {
  value       = "http://kube-prometheus-stack-alertmanager.${var.namespace}.svc.cluster.local:9093"
  description = "In-cluster Alertmanager API endpoint."
}
