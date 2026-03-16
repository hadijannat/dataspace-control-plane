variable "cluster_name" {
  type    = string
  default = "prod-eu"
}

variable "registry_storage_gb" {
  type    = number
  default = 200
}

variable "external_registry_url" {
  type    = string
  default = "registry.prod-eu.example.internal/dataspace"
}
