output "host" {
  value       = var.mode == "dev-scaffold" ? "${var.instance_name}-postgres.${var.namespace}.svc.cluster.local" : var.external_host
  description = "Fully qualified in-cluster hostname for the Postgres service."
}

output "port" {
  value       = var.mode == "dev-scaffold" ? 5432 : var.external_port
  description = "Postgres service port."
}

output "database_name" {
  value       = var.database_name
  description = "Name of the Postgres database."
}

output "secret_name" {
  value       = var.mode == "dev-scaffold" ? kubernetes_secret.postgres_credentials[0].metadata[0].name : var.external_secret_name
  description = "Name of the K8s Secret containing Postgres credentials. Reference this in Helm values as postgresSecretName."
}
