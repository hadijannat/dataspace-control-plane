variable "namespace" {
  type        = string
  description = "Kubernetes namespace where Keycloak will be deployed."
}

variable "mode" {
  type        = string
  default     = "external"
  description = "Infrastructure ownership mode: dev-scaffold deploys in-cluster Keycloak, external references a durable shared identity service."

  validation {
    condition     = contains(["dev-scaffold", "external"], var.mode)
    error_message = "mode must be one of: dev-scaffold, external."
  }
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

variable "external_service_name" {
  type        = string
  default     = "keycloak"
  description = "Service name or reference label when mode=external."
}

variable "external_admin_url" {
  type        = string
  default     = "https://keycloak.example.com/admin"
  description = "External Keycloak admin URL when mode=external."
}

variable "external_realm_url" {
  type        = string
  default     = "https://keycloak.example.com/realms/dataspace"
  description = "External Keycloak realm discovery URL when mode=external."
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to all resources."
}
