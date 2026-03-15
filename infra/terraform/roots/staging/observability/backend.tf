terraform {
  backend "kubernetes" {
    secret_suffix = "staging-observability"
    namespace     = "terraform-state"
  }
}
