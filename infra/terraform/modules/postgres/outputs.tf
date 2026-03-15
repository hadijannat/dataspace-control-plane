output "host" {
  value       = "${var.instance_name}-postgres.${var.namespace}.svc.cluster.local"
  description = "Fully qualified in-cluster hostname for the Postgres service."
}

output "port" {
  value       = 5432
  description = "Postgres service port."
}

output "database_name" {
  value       = var.database_name
  description = "Name of the Postgres database."
}

output "secret_name" {
  value       = kubernetes_secret.postgres_credentials.metadata[0].name
  description = "Name of the K8s Secret containing Postgres credentials. Reference this in Helm values as postgresSecretName."
}
