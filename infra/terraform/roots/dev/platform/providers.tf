provider "kubernetes" {
  # Auth via KUBECONFIG env var or in-cluster service account.
  # config_path = var.kubeconfig_path  # uncomment for local dev with explicit kubeconfig
}

provider "helm" {
  kubernetes {
    # Same auth as kubernetes provider above.
  }
}
