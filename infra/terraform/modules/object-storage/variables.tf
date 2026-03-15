variable "bucket_name" {
  type        = string
  description = "Name of the object storage bucket."

  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", var.bucket_name)) && length(var.bucket_name) <= 63
    error_message = "Bucket name must be 1-63 lowercase alphanumeric characters or hyphens."
  }
}

variable "region" {
  type        = string
  description = "Cloud region for the bucket (e.g. eu-west-1, europe-west1, westeurope)."
}

variable "versioning_enabled" {
  type        = bool
  default     = true
  description = "Enable object versioning for point-in-time recovery."
}

variable "labels" {
  type        = map(string)
  default     = {}
  description = "Labels/tags to apply to the bucket resource."
}
