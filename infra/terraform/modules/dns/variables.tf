variable "zone_name" {
  type        = string
  description = "DNS zone name (e.g. eu.dataspace.example.com)."
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
