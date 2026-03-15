terraform {
  backend "kubernetes" {
    secret_suffix = "staging-platform"
    namespace     = "terraform-state"
  }
}
