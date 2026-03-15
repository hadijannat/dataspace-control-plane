output "vault_addr" {
  value       = var.mode == "dev-scaffold" ? "http://vault.${var.namespace}.svc.cluster.local:8200" : var.external_vault_addr
  description = "In-cluster Vault API address."
}

output "service_name" {
  value       = var.mode == "dev-scaffold" ? kubernetes_service.vault[0].metadata[0].name : var.external_service_name
  description = "Kubernetes Service name for Vault."
}

output "root_token_secret_name" {
  value       = var.mode == "dev-scaffold" ? "vault-dev-token" : var.external_root_token_secret_name
  description = <<-DESC
    Name of the K8s Secret that contains the Vault root token (dev environments only).
    NOTE: This is the Secret NAME only — never the token value.
    In production, the root token is not persisted; unseal keys are stored in HSM or cloud KMS.
  DESC
}
