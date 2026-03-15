# PRODUCTION: Auth must use OIDC-based workload identity or service account tokens.
# DO NOT use developer kubeconfig files or long-lived credentials for production.
# Configure via KUBECONFIG env var pointing to a role-restricted kubeconfig,
# or use in-cluster service account with minimal permissions.
#
# Example (GKE Workload Identity):
#   Configure GOOGLE_APPLICATION_CREDENTIALS to a service account key
#   bound to a K8s service account with limited permissions.
#
# Example (EKS IRSA):
#   Configure AWS_ROLE_ARN and AWS_WEB_IDENTITY_TOKEN_FILE for IRSA.

provider "kubernetes" {
  # Auth via KUBECONFIG env var (restricted role) or in-cluster service account.
  # config_path = var.kubeconfig_path  # uncomment only for operator access
}

provider "helm" {
  kubernetes {}
}
