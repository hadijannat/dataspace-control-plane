variable "namespace" {
  type        = string
  description = "Kubernetes namespace where Vault will be deployed."
}

variable "mode" {
  type        = string
  default     = "external"
  description = "Infrastructure ownership mode: dev-scaffold deploys an in-cluster Vault for local work, external references a durable shared service."

  validation {
    condition     = contains(["dev-scaffold", "external"], var.mode)
    error_message = "mode must be one of: dev-scaffold, external."
  }
}

variable "storage_size" {
  type        = string
  default     = "10Gi"
  description = "Persistent volume claim size for Vault data."
}

variable "ha_enabled" {
  type        = bool
  default     = false
  description = "Enable Vault HA mode (requires Raft storage and 3+ replicas). Set to true for staging/prod."
}

variable "transit_enabled" {
  type        = bool
  default     = true
  description = "Enable the Vault Transit secrets engine (used for envelope encryption)."
}

variable "pki_enabled" {
  type        = bool
  default     = true
  description = "Enable the Vault PKI secrets engine (used for internal certificate issuance)."
}

variable "external_vault_addr" {
  type        = string
  default     = "https://vault.example.com"
  description = "Vault API address when mode=external."
}

variable "external_service_name" {
  type        = string
  default     = "vault"
  description = "Service name or reference label when mode=external."
}

variable "external_root_token_secret_name" {
  type        = string
  default     = null
  description = "Optional existing Kubernetes Secret name for development-only root token handling when mode=external."
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to all resources."
}
