variable "namespace" {
  type    = string
  default = "dataspace"
}

variable "postgres_storage_size" {
  type    = string
  default = "100Gi"
}

variable "vault_storage_size" {
  type    = string
  default = "50Gi"
}

variable "ingress_class_name" {
  type    = string
  default = "nginx"
}

variable "object_storage_bucket" {
  type    = string
  default = "dataspace-prod-eu-artifacts"
}

variable "object_storage_region" {
  type    = string
  default = "eu-west-1"
}
