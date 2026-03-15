output "registry_url" {
  value       = "REPLACE_WITH_PROVIDER_REGISTRY_URL"
  description = "URL of the container registry. Update after substituting the provider-specific resource."
}

output "registry_name" {
  value       = var.name
  description = "Name of the registry project or repository."
}
