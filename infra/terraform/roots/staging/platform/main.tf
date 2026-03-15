# staging/platform — Postgres, Keycloak, Vault, ingress for staging.

locals {
  env_labels = {
    "environment"               = "staging"
    "app.kubernetes.io/part-of" = "dataspace-control-plane"
  }
}

module "postgres" {
  source = "../../../modules/postgres"

  mode           = "external"
  instance_name  = "dataspace"
  namespace      = var.namespace
  database_name  = "dataspace"
  username       = "dataspace"
  storage_size   = var.postgres_storage_size
  version        = "16"
  backup_enabled = true
  external_host        = var.external_postgres_host
  external_secret_name = var.external_postgres_secret_name
  labels         = local.env_labels
}

module "keycloak" {
  source = "../../../modules/keycloak"

  mode                  = "external"
  namespace         = var.namespace
  realm_name        = "dataspace"
  admin_secret_name = "keycloak-admin-credentials"
  storage_size      = "5Gi"
  external_service_name = var.external_keycloak_service_name
  external_admin_url    = var.external_keycloak_admin_url
  external_realm_url    = var.external_keycloak_realm_url
  labels            = local.env_labels
}

module "vault" {
  source = "../../../modules/vault"

  mode               = "external"
  namespace       = var.namespace
  storage_size    = var.vault_storage_size
  ha_enabled      = false
  transit_enabled = true
  pki_enabled     = true
  external_vault_addr   = var.external_vault_addr
  external_service_name = var.external_vault_service_name
  labels          = local.env_labels
}

module "ingress" {
  source = "../../../modules/ingress"

  namespace  = "ingress-nginx"
  class_name = var.ingress_class_name
  replicas   = 2
  labels     = local.env_labels
}
