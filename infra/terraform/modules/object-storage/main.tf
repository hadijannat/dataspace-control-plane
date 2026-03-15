# object-storage module
#
# Replace this placeholder with your cloud provider's storage resource:
#   - AWS S3:          aws_s3_bucket + aws_s3_bucket_versioning + aws_s3_bucket_server_side_encryption_configuration
#   - GCP GCS:         google_storage_bucket
#   - Azure Blob:      azurerm_storage_account + azurerm_storage_container
#   - MinIO (K8s):     kubernetes_deployment + PVC (not recommended for production data)
#
# Policy enforcement: see infra/terraform/policy/no_public_s3.rego
# — buckets must NOT have public ACLs. This is enforced by OPA at plan time.

locals {
  bucket_config = {
    name               = var.bucket_name
    region             = var.region
    versioning_enabled = var.versioning_enabled
    labels             = var.labels
  }
}

# Placeholder: documents the intended bucket configuration.
# Replace with actual provider resource after provider selection.
resource "local_file" "bucket_config" {
  filename = "${path.module}/.bucket-config-${var.bucket_name}.json"
  content = jsonencode({
    bucket_name        = var.bucket_name
    region             = var.region
    versioning_enabled = var.versioning_enabled
    labels             = var.labels
    note               = "Replace this local_file resource with your cloud provider bucket resource. See module README."
  })
}
