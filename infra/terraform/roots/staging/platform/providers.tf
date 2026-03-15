provider "kubernetes" {
  # Auth via KUBECONFIG env var or in-cluster service account.
}

provider "helm" {
  kubernetes {}
}
