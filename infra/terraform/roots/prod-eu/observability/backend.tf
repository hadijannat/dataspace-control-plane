terraform {
  backend "kubernetes" {
    secret_suffix = "prod-eu-observability"
    namespace     = "terraform-state"
  }
}
