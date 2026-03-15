# dev/bootstrap — Run first in the dev environment.
# Creates the dataspace namespace and container registry prerequisites.
# All platform/ and observability/ roots depend on the namespace created here.

module "dataspace_namespace" {
  source = "../../../modules/kubernetes-namespace"

  name = "dataspace"
  labels = {
    "environment"               = "dev"
    "app.kubernetes.io/part-of" = "dataspace-control-plane"
    "cluster"                   = var.cluster_name
  }
  annotations = {
    "infra.dataspace.io/managed-by" = "terraform"
    "infra.dataspace.io/env"        = "dev"
  }
}

module "terraform_state_namespace" {
  source = "../../../modules/kubernetes-namespace"

  name = "terraform-state"
  labels = {
    "environment"               = "dev"
    "app.kubernetes.io/part-of" = "terraform"
  }
}

module "dev_registry" {
  source = "../../../modules/registry"

  name             = "dataspace-dev"
  namespace        = module.dataspace_namespace.name
  storage_limit_gb = var.registry_storage_gb
  labels = {
    "environment" = "dev"
    "cluster"     = var.cluster_name
  }
}
