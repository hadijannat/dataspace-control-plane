variable "name" {
  type        = string
  description = "Registry project or repository name."
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

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to resources."
}
