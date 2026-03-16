# registry module
# Generic container registry configuration.
#
# Replace this resource with your registry provider resource depending on your setup:
#   - Harbor:  harbor_project resource (registry.terraform.io/goharbor/harbor)
#   - AWS ECR: aws_ecr_repository resource (registry.terraform.io/hashicorp/aws)
#   - GCP GAR: google_artifact_registry_repository (registry.terraform.io/hashicorp/google)
#   - Azure ACR: azurerm_container_registry (registry.terraform.io/hashicorp/azurerm)
#
# The dev-scaffold mode records the local registry contract in-cluster.
# Shared environments should use mode=external and pass a concrete registry URL.

locals {
  scaffold_enabled      = var.mode == "dev-scaffold"
  scaffold_registry_url = "registry.local/${var.name}"
}

resource "kubernetes_config_map" "registry_config" {
  count = local.scaffold_enabled ? 1 : 0

  metadata {
    name      = "${var.name}-registry-config"
    namespace = var.namespace
    labels = merge(
      {
        "app.kubernetes.io/managed-by" = "terraform"
        "app.kubernetes.io/component"  = "registry"
      },
      var.labels
    )
  }

  data = {
    "registry.name"             = var.name
    "registry.storage_limit_gb" = tostring(var.storage_limit_gb)
    "registry.url"              = local.scaffold_registry_url
  }
}
