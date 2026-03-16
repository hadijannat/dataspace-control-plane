variable "name" {
  type        = string
  description = "Registry project or repository name."
}

variable "mode" {
  type        = string
  default     = "external"
  description = "Infrastructure ownership mode: dev-scaffold records a local registry contract in-cluster, external references a durable shared registry."

  validation {
    condition     = contains(["dev-scaffold", "external"], var.mode)
    error_message = "mode must be one of: dev-scaffold, external."
  }
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace where the registry config ConfigMap will be created."
}

variable "storage_limit_gb" {
  type        = number
  default     = 50
  description = "Storage limit for the registry in gigabytes (used by provider-specific resources)."

  validation {
    condition     = var.storage_limit_gb >= 1 && var.storage_limit_gb <= 10000
    error_message = "storage_limit_gb must be between 1 and 10000."
  }
}

variable "external_registry_url" {
  type        = string
  default     = "registry.example.internal/dataspace"
  description = "Registry URL when mode=external."
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to resources."
}
