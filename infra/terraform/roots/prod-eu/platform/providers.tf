# PRODUCTION: Auth must use OIDC-based workload identity.
# DO NOT use developer kubeconfig files for production state access.

provider "kubernetes" {
  # Auth via KUBECONFIG env var pointing to restricted role kubeconfig,
  # or in-cluster service account with minimal permissions.
}

provider "helm" {
  kubernetes {}
}
