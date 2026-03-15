terraform {
  backend "kubernetes" {
    secret_suffix = "dev-observability"
    namespace     = "terraform-state"
  }
}
