variable "namespace" {
  type        = string
  description = "Kubernetes namespace where Keycloak will be deployed."
}

variable "realm_name" {
  type        = string
  description = "Default Keycloak realm name."
}

variable "admin_secret_name" {
  type        = string
  description = "Name of the K8s Secret that holds the Keycloak admin credentials. Must be pre-created or injected by Vault/ESO."
}

variable "storage_size" {
  type        = string
  default     = "5Gi"
  description = "Persistent volume claim size for Keycloak embedded H2 or theme storage."
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to all resources."
}
