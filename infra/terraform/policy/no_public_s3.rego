package terraform.policy

# Deny S3 buckets with public-read ACL.
# Enforces data sovereignty and confidentiality for the dataspace control plane.
# All S3 buckets must be private — public access must be routed through CDN or signed URLs.

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  resource.change.after.acl == "public-read"
  msg := sprintf(
    "S3 bucket '%v' must not have public-read ACL. All buckets must be private. Use CloudFront or pre-signed URLs for public access.",
    [resource.address]
  )
}

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  resource.change.after.acl == "public-read-write"
  msg := sprintf(
    "S3 bucket '%v' must not have public-read-write ACL. This is never permitted.",
    [resource.address]
  )
}

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  resource.change.after.acl == "authenticated-read"
  msg := sprintf(
    "S3 bucket '%v' must not use authenticated-read ACL. Use IAM policies for access control instead.",
    [resource.address]
  )
}

# Deny if public_access_block_configuration is explicitly disabled
deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket_public_access_block"
  resource.change.after.block_public_acls == false
  msg := sprintf(
    "S3 public access block '%v' must not disable block_public_acls.",
    [resource.address]
  )
}

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket_public_access_block"
  resource.change.after.block_public_policy == false
  msg := sprintf(
    "S3 public access block '%v' must not disable block_public_policy.",
    [resource.address]
  )
}
