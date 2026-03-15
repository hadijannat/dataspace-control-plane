output "name" {
  value       = kubernetes_namespace.this.metadata[0].name
  description = "The name of the created Kubernetes namespace."
}

output "uid" {
  value       = kubernetes_namespace.this.metadata[0].uid
  description = "The UID of the created Kubernetes namespace."
}
