variable "zone_name" {
  type        = string
  description = "DNS zone name (e.g. eu.dataspace.example.com)."
}

variable "mode" {
  type        = string
  default     = "external"
  description = "Infrastructure ownership mode. DNS is represented as an external durable dependency in this provider-neutral module."

  validation {
    condition     = contains(["dev-scaffold", "external"], var.mode)
    error_message = "mode must be one of: dev-scaffold, external."
  }
}

variable "records" {
  type = list(object({
    name  = string
    type  = string
    value = string
    ttl   = number
  }))
  default     = []
  description = "List of DNS records to create in the zone."
}

variable "external_zone_id" {
  type        = string
  default     = "zone-example"
  description = "Existing DNS zone identifier when mode=external."
}
