variable "instance_name" {
  type        = string
  description = "Name identifier for this Postgres instance."
}

variable "mode" {
  type        = string
  default     = "external"
  description = "Infrastructure ownership mode: dev-scaffold creates an in-cluster Postgres, external references a durable external service."

  validation {
    condition     = contains(["dev-scaffold", "external"], var.mode)
    error_message = "mode must be one of: dev-scaffold, external."
  }
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace where Postgres resources will be created."
}

variable "database_name" {
  type        = string
  description = "Name of the default database to create."
}

variable "username" {
  type        = string
  description = "Postgres superuser username."
}

variable "storage_size" {
  type        = string
  default     = "10Gi"
  description = "Persistent volume claim size for Postgres data (e.g. 10Gi, 100Gi)."
}

variable "version" {
  type        = string
  default     = "16"
  description = "Postgres major version (e.g. 16, 15)."
}

variable "backup_enabled" {
  type        = bool
  default     = true
  description = "Whether to enable automated backups. Managed by provider-specific resource when substituted."
}

variable "external_host" {
  type        = string
  default     = "postgres.example.internal"
  description = "External Postgres hostname when mode=external."
}

variable "external_port" {
  type        = number
  default     = 5432
  description = "External Postgres port when mode=external."
}

variable "external_secret_name" {
  type        = string
  default     = "postgres-credentials"
  description = "Existing Kubernetes Secret name that Helm charts should reference when mode=external."
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to all resources."
}
