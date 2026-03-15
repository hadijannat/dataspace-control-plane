terraform {
  backend "kubernetes" {
    # Secret-based state storage for dev. For prod, use S3/GCS/Azure Blob.
    # Configure via: terraform init -backend-config=../../../backends/dev.backend.hcl
    secret_suffix = "dev-bootstrap"
    namespace     = "terraform-state"
  }
}
