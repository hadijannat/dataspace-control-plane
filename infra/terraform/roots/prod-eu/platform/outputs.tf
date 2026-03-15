output "postgres_host" {
  value = module.postgres.host
}

output "keycloak_admin_url" {
  value = module.keycloak.admin_url
}

output "vault_addr" {
  value = module.vault.vault_addr
}

output "ingress_class_name" {
  value = module.ingress.class_name
}

output "object_storage_bucket" {
  value = module.object_storage.bucket_name
}
