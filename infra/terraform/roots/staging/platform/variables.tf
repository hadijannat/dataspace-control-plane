variable "namespace" {
  type    = string
  default = "dataspace"
}

variable "postgres_storage_size" {
  type    = string
  default = "20Gi"
}

variable "vault_storage_size" {
  type    = string
  default = "10Gi"
}

variable "ingress_class_name" {
  type    = string
  default = "nginx"
}
