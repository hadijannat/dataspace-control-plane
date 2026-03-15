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

  instance_name  = "dataspace"
  namespace      = var.namespace
  database_name  = "dataspace"
  username       = "dataspace"
  storage_size   = var.postgres_storage_size
  version        = "16"
  backup_enabled = true
  labels         = local.env_labels
}

module "keycloak" {
  source = "../../../modules/keycloak"

  namespace         = var.namespace
  realm_name        = "dataspace"
  admin_secret_name = "keycloak-admin-credentials"
  storage_size      = "20Gi"
  labels            = local.env_labels
}

module "vault" {
  source = "../../../modules/vault"

  namespace       = var.namespace
  storage_size    = var.vault_storage_size
  ha_enabled      = true
  transit_enabled = true
  pki_enabled     = true
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

  bucket_name        = var.object_storage_bucket
  region             = var.object_storage_region
  versioning_enabled = true
  labels             = local.env_labels
}
