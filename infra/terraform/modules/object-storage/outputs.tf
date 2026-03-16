output "bucket_name" {
  value       = var.bucket_name
  description = "Name of the object storage bucket."
}

output "bucket_url" {
  value       = var.external_bucket_url
  description = "URL of the bucket (e.g. s3://bucket-name, gs://bucket-name)."
}
