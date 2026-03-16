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

variable "external_postgres_host" {
  type    = string
  default = "postgres.staging.example.internal"
}

variable "external_postgres_secret_name" {
  type    = string
  default = "control-plane-postgres-staging"
}

variable "external_keycloak_service_name" {
  type    = string
  default = "keycloak-staging"
}

variable "external_keycloak_admin_url" {
  type    = string
  default = "https://keycloak.staging.example.com/admin"
}

variable "external_keycloak_realm_url" {
  type    = string
  default = "https://keycloak.staging.example.com/realms/dataspace"
}

variable "external_vault_addr" {
  type    = string
  default = "https://vault.staging.example.com"
}

variable "external_vault_service_name" {
  type    = string
  default = "vault-staging"
}
