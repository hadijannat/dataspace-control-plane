variable "name" {
  type        = string
  description = "The name of the Kubernetes namespace to create."

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", var.name))
    error_message = "Namespace name must be a valid DNS label (lowercase alphanumeric and hyphens, starting and ending with alphanumeric)."
  }
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to the namespace metadata."
}

variable "annotations" {
  type        = map(string)
  default     = {}
  description = "Annotations to apply to the namespace metadata."
}
