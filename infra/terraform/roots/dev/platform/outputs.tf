output "postgres_host" {
  value       = module.postgres.host
  description = "In-cluster Postgres hostname."
}

output "keycloak_admin_url" {
  value       = module.keycloak.admin_url
  description = "Keycloak admin console URL."
}

output "vault_addr" {
  value       = module.vault.vault_addr
  description = "In-cluster Vault API address."
}

output "ingress_class_name" {
  value       = module.ingress.class_name
  description = "IngressClass name for Helm chart references."
}
