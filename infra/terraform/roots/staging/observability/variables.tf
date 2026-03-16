variable "namespace" {
  type    = string
  default = "observability"
}

variable "grafana_admin_secret_name" {
  type    = string
  default = "grafana-admin-staging"
}
