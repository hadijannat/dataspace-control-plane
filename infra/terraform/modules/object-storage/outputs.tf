output "bucket_name" {
  value       = var.bucket_name
  description = "Name of the object storage bucket."
}

output "bucket_url" {
  value       = "REPLACE_WITH_PROVIDER_BUCKET_URL"
  description = "URL of the bucket (e.g. s3://bucket-name, gs://bucket-name). Update after provider substitution."
}
