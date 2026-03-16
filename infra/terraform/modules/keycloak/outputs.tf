output "service_name" {
  value       = var.mode == "dev-scaffold" ? kubernetes_service.keycloak[0].metadata[0].name : var.external_service_name
  description = "Kubernetes Service name for Keycloak."
}

output "admin_url" {
  value       = var.mode == "dev-scaffold" ? "http://keycloak.${var.namespace}.svc.cluster.local:8080/admin" : var.external_admin_url
  description = "Keycloak admin console URL (in-cluster)."
}

output "realm_url" {
  value       = var.mode == "dev-scaffold" ? "http://keycloak.${var.namespace}.svc.cluster.local:8080/realms/${var.realm_name}" : var.external_realm_url
  description = "Keycloak realm discovery URL (in-cluster)."
}
