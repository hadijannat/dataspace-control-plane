output "vault_addr" {
  value       = "http://vault.${var.namespace}.svc.cluster.local:8200"
  description = "In-cluster Vault API address."
}

output "service_name" {
  value       = kubernetes_service.vault.metadata[0].name
  description = "Kubernetes Service name for Vault."
}

output "root_token_secret_name" {
  value       = "vault-dev-token"
  description = <<-DESC
    Name of the K8s Secret that contains the Vault root token (dev environments only).
    NOTE: This is the Secret NAME only — never the token value.
    In production, the root token is not persisted; unseal keys are stored in HSM or cloud KMS.
  DESC
}
