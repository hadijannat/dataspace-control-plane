# prod-eu/platform — Production EU platform services.
# Postgres 100Gi, Vault HA (3 replicas), ingress 3 replicas, object storage.

locals {
  env_labels = {
    "environment"               = "prod-eu"
    "app.kubernetes.io/part-of" = "dataspace-control-plane"
    "region"                    = "eu"
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
  storage_size      = "20Gi"
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
  ha_enabled      = true
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
  replicas   = 3
  labels     = local.env_labels
}

module "object_storage" {
  source = "../../../modules/object-storage"

  mode               = "external"
  bucket_name        = var.object_storage_bucket
  region             = var.object_storage_region
  versioning_enabled = true
  external_bucket_url = var.external_object_storage_url
  labels             = local.env_labels
}
