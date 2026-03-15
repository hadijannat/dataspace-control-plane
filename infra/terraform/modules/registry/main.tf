# registry module
# Generic container registry configuration.
#
# Replace this resource with your registry provider resource depending on your setup:
#   - Harbor:  harbor_project resource (registry.terraform.io/goharbor/harbor)
#   - AWS ECR: aws_ecr_repository resource (registry.terraform.io/hashicorp/aws)
#   - GCP GAR: google_artifact_registry_repository (registry.terraform.io/hashicorp/google)
#   - Azure ACR: azurerm_container_registry (registry.terraform.io/hashicorp/azurerm)
#
# This placeholder creates a ConfigMap documenting the registry configuration.
# It does not create an actual registry — substitute as appropriate.

resource "kubernetes_config_map" "registry_config" {
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
    # NOTE: registry URL is set per-provider; update after substituting provider resource above
    "registry.url" = "REPLACE_WITH_PROVIDER_REGISTRY_URL"
  }
}
