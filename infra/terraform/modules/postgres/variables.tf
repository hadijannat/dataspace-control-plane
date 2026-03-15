variable "instance_name" {
  type        = string
  description = "Name identifier for this Postgres instance."
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

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to all resources."
}
