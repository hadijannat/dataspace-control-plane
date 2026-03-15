# prod-eu/bootstrap — Creates namespace and registry for production EU.

module "dataspace_namespace" {
  source = "../../../modules/kubernetes-namespace"

  name = "dataspace"
  labels = {
    "environment"               = "prod-eu"
    "app.kubernetes.io/part-of" = "dataspace-control-plane"
    "cluster"                   = var.cluster_name
    "region"                    = "eu"
  }
  annotations = {
    "infra.dataspace.io/managed-by" = "terraform"
    "infra.dataspace.io/env"        = "prod-eu"
  }
}

module "terraform_state_namespace" {
  source = "../../../modules/kubernetes-namespace"
  name   = "terraform-state"
  labels = { "environment" = "prod-eu" }
}

module "prod_eu_registry" {
  source = "../../../modules/registry"

  name             = "dataspace-prod-eu"
  namespace        = module.dataspace_namespace.name
  storage_limit_gb = var.registry_storage_gb
  labels = {
    "environment" = "prod-eu"
    "region"      = "eu"
  }
}
