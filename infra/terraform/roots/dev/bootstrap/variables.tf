variable "cluster_name" {
  type        = string
  default     = "dev"
  description = "Kubernetes cluster name — used for labeling and naming."
}

variable "registry_storage_gb" {
  type        = number
  default     = 20
  description = "Storage limit for the dev container registry in GB."
}
