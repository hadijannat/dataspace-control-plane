variable "namespace" {
  type        = string
  description = "Kubernetes namespace for the observability stack."
}

variable "prometheus_storage_size" {
  type        = string
  default     = "50Gi"
  description = "Persistent volume size for Prometheus TSDB."
}

variable "grafana_enabled" {
  type        = bool
  default     = true
  description = "Deploy Grafana alongside Prometheus."
}

variable "loki_enabled" {
  type        = bool
  default     = false
  description = "Deploy Grafana Loki for log aggregation."
}

variable "tempo_enabled" {
  type        = bool
  default     = false
  description = "Deploy Grafana Tempo for distributed trace storage."
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels to apply to all observability resources."
}
