variable "cluster_name" {
  type    = string
  default = "staging"
}

variable "registry_storage_gb" {
  type    = number
  default = 50
}

variable "external_registry_url" {
  type    = string
  default = "registry.staging.example.internal/dataspace"
}
