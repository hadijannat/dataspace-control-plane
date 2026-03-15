variable "namespace" {
  type        = string
  description = "Kubernetes namespace where Vault will be deployed."
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

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to all resources."
}
