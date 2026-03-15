variable "namespace" {
  type        = string
  default     = "dataspace"
  description = "Target Kubernetes namespace (must already exist — created by bootstrap root)."
}

variable "postgres_storage_size" {
  type        = string
  default     = "5Gi"
  description = "Postgres PVC size for dev environment."
}

variable "vault_storage_size" {
  type        = string
  default     = "5Gi"
  description = "Vault PVC size for dev environment."
}

variable "ingress_class_name" {
  type        = string
  default     = "nginx"
  description = "IngressClass name for the NGINX controller."
}
