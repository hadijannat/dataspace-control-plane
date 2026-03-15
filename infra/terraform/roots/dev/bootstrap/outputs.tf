output "namespace_name" {
  value       = module.dataspace_namespace.name
  description = "The name of the dataspace Kubernetes namespace."
}

output "registry_url" {
  value       = module.dev_registry.registry_url
  description = "URL of the dev container registry."
}
