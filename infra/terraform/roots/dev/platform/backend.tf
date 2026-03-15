terraform {
  backend "kubernetes" {
    # Configure via: terraform init -backend-config=../../../backends/dev.backend.hcl
    secret_suffix = "dev-platform"
    namespace     = "terraform-state"
  }
}
