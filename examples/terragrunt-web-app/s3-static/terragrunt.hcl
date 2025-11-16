# S3 Static Content Bucket - Pure Terragrunt Configuration
# Directly uses terraform-aws-modules/s3-bucket/aws

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "aws_config" {
  config_path = "../aws-config"
  skip_outputs = true
}

terraform {
  source = "tfr:///terraform-aws-modules/s3-bucket/aws?version=4.2.0"
}

inputs = {
  bucket = "web-app-static-${get_aws_account_id()}"

  # Versioning
  versioning = {
    enabled = true
  }

  # Allow Terraform to destroy bucket with objects and versions
  force_destroy = true

  # Server-side encryption
  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
      bucket_key_enabled = true
    }
  }

  # Block public access
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  # Lifecycle rules
  lifecycle_rule = [
    {
      id      = "transition-and-expiration"
      enabled = true

      transition = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = 365
      }

      noncurrent_version_expiration = {
        noncurrent_days = 90
      }
    }
  ]

  tags = merge(
    include.root.locals.common_tags,
    {
      Name = "web-app-static-content"
      Tier = "storage"
      Role = "static-assets"
    }
  )
}
