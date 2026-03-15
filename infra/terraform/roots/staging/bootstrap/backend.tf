terraform {
  backend "kubernetes" {
    secret_suffix = "staging-bootstrap"
    namespace     = "terraform-state"
  }
}
