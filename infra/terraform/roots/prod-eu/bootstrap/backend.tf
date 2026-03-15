terraform {
  backend "kubernetes" {
    # For prod, use S3/GCS/Azure Blob backend with MFA-protected access.
    # Configure via: terraform init -backend-config=../../../backends/prod-eu.backend.hcl
    secret_suffix = "prod-eu-bootstrap"
    namespace     = "terraform-state"
  }
}
