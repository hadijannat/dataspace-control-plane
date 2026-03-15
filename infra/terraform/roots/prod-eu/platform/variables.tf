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

variable "external_postgres_host" {
  type    = string
  default = "postgres.prod-eu.example.internal"
}

variable "external_postgres_secret_name" {
  type    = string
  default = "control-plane-postgres-prod-eu"
}

variable "external_keycloak_service_name" {
  type    = string
  default = "keycloak-prod-eu"
}

variable "external_keycloak_admin_url" {
  type    = string
  default = "https://keycloak.eu.example.com/admin"
}

variable "external_keycloak_realm_url" {
  type    = string
  default = "https://keycloak.eu.example.com/realms/dataspace"
}

variable "external_vault_addr" {
  type    = string
  default = "https://vault.eu.example.com"
}

variable "external_vault_service_name" {
  type    = string
  default = "vault-prod-eu"
}

variable "external_object_storage_url" {
  type    = string
  default = "s3://dataspace-prod-eu-artifacts"
}
