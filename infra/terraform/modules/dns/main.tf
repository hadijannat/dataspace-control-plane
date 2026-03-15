# dns module
#
# Replace this placeholder with your DNS provider resource:
#   - AWS Route53:        aws_route53_record + aws_route53_zone
#   - GCP Cloud DNS:      google_dns_record_set + google_dns_managed_zone
#   - Cloudflare:         cloudflare_record + cloudflare_zone
#   - Azure DNS:          azurerm_dns_record_set + azurerm_dns_zone

locals {
  records_map = {
    for r in var.records : "${r.name}-${r.type}" => r
  }
}

# Placeholder: documents the DNS configuration.
# Replace with provider-specific resources after DNS provider selection.
resource "local_file" "dns_config" {
  filename = "${path.module}/.dns-config-${replace(var.zone_name, ".", "-")}.json"
  content = jsonencode({
    zone_name = var.zone_name
    records   = var.records
    note      = "Replace this local_file resource with your DNS provider resources. See module README."
  })
}
