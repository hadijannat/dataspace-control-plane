# dev/platform — Run after bootstrap/.
# Deploys shared platform services: Postgres, Keycloak, Vault, ingress controller.

locals {
  env_labels = {
    "environment"               = "dev"
    "app.kubernetes.io/part-of" = "dataspace-control-plane"
  }
}

module "postgres" {
  source = "../../../modules/postgres"

  mode          = "dev-scaffold"
  instance_name = "dataspace"
  namespace     = var.namespace
  database_name = "dataspace"
  username      = "dataspace"
  storage_size  = var.postgres_storage_size
  version       = "16"
  backup_enabled = false  # Dev: no backup needed
  labels        = local.env_labels
}

module "keycloak" {
  source = "../../../modules/keycloak"

  mode              = "dev-scaffold"
  namespace         = var.namespace
  realm_name        = "dataspace"
  admin_secret_name = "keycloak-admin-credentials"
  storage_size      = "5Gi"
  labels            = local.env_labels
}

module "vault" {
  source = "../../../modules/vault"

  mode            = "dev-scaffold"
  namespace       = var.namespace
  storage_size    = var.vault_storage_size
  ha_enabled      = false
  transit_enabled = true
  pki_enabled     = true
  labels          = local.env_labels
}

module "ingress" {
  source = "../../../modules/ingress"

  namespace  = "ingress-nginx"
  class_name = var.ingress_class_name
  replicas   = 1
  labels     = local.env_labels
}
