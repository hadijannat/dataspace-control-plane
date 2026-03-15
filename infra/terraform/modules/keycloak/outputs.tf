output "service_name" {
  value       = kubernetes_service.keycloak.metadata[0].name
  description = "Kubernetes Service name for Keycloak."
}

output "admin_url" {
  value       = "http://keycloak.${var.namespace}.svc.cluster.local:8080/admin"
  description = "Keycloak admin console URL (in-cluster)."
}

output "realm_url" {
  value       = "http://keycloak.${var.namespace}.svc.cluster.local:8080/realms/${var.realm_name}"
  description = "Keycloak realm discovery URL (in-cluster)."
}
