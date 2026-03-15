# staging/bootstrap — Creates namespace and registry prerequisites.

module "dataspace_namespace" {
  source = "../../../modules/kubernetes-namespace"

  name = "dataspace"
  labels = {
    "environment"               = "staging"
    "app.kubernetes.io/part-of" = "dataspace-control-plane"
    "cluster"                   = var.cluster_name
  }
}

module "terraform_state_namespace" {
  source = "../../../modules/kubernetes-namespace"
  name   = "terraform-state"
  labels = { "environment" = "staging" }
}

module "staging_registry" {
  source = "../../../modules/registry"

  name             = "dataspace-staging"
  namespace        = module.dataspace_namespace.name
  storage_limit_gb = var.registry_storage_gb
  labels           = { "environment" = "staging" }
}
