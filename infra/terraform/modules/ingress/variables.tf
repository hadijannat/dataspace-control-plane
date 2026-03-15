variable "namespace" {
  type        = string
  description = "Kubernetes namespace where the ingress controller will be deployed."
}

variable "class_name" {
  type        = string
  default     = "nginx"
  description = "IngressClass name for the controller."
}

variable "replicas" {
  type        = number
  default     = 2
  description = "Number of ingress controller replicas."

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 10
    error_message = "replicas must be between 1 and 10."
  }
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to resources created by this module."
}
