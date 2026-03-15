output "registry_url" {
  value       = var.mode == "dev-scaffold" ? local.scaffold_registry_url : var.external_registry_url
  description = "URL of the container registry."
}

output "registry_name" {
  value       = var.name
  description = "Name of the registry project or repository."
}
