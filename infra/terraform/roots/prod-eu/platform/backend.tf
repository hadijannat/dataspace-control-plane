terraform {
  backend "kubernetes" {
    # For prod-eu, use S3/GCS/Azure Blob with MFA-protected IAM role.
    # Configure via: terraform init -backend-config=../../../backends/prod-eu.backend.hcl
    secret_suffix = "prod-eu-platform"
    namespace     = "terraform-state"
  }
}
