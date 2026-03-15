output "zone_id" {
  value       = "REPLACE_WITH_PROVIDER_ZONE_ID"
  description = "DNS zone ID (update after provider substitution)."
}

output "zone_name" {
  value       = var.zone_name
  description = "DNS zone name."
}
