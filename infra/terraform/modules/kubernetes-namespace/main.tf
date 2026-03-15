# kubernetes-namespace module
# Creates a Kubernetes namespace with optional labels and annotations.
# No provider block — inherited from the calling root module.

resource "kubernetes_namespace" "this" {
  metadata {
    name        = var.name
    labels      = merge(
      {
        "app.kubernetes.io/managed-by" = "terraform"
      },
      var.labels
    )
    annotations = var.annotations
  }
}
