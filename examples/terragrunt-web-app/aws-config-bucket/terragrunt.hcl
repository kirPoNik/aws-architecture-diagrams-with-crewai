# AWS Config S3 Bucket - Pure Terragrunt Configuration
# Dedicated S3 bucket for AWS Config snapshots and history
# Directly uses terraform-aws-modules/s3-bucket/aws

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

terraform {
  source = "tfr:///terraform-aws-modules/s3-bucket/aws?version=4.2.0"
}

inputs = {
  bucket = "aws-config-${get_aws_account_id()}"

  # Versioning
  versioning = {
    enabled = true
  }

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
  block_public_policy     = false  # Allow bucket policy for AWS Config
  ignore_public_acls      = true
  restrict_public_buckets = true

  # Bucket policy for AWS Config
  attach_policy = true
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSConfigBucketPermissionsCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = "arn:aws:s3:::aws-config-${get_aws_account_id()}"
      },
      {
        Sid    = "AWSConfigBucketExistenceCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:ListBucket"
        Resource = "arn:aws:s3:::aws-config-${get_aws_account_id()}"
      },
      {
        Sid    = "AWSConfigBucketPutObject"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "arn:aws:s3:::aws-config-${get_aws_account_id()}/AWSLogs/${get_aws_account_id()}/Config/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })

  # Lifecycle rules for Config snapshots (compliance retention)
  lifecycle_rule = [
    {
      id      = "config-retention"
      enabled = true

      transition = [
        {
          days          = 90
          storage_class = "STANDARD_IA"
        },
        {
          days          = 180
          storage_class = "GLACIER"
        }
      ]

      expiration = {
        days = 2555  # ~7 years for compliance
      }
    }
  ]

  tags = {
      Name = "aws-config-bucket"
      Tier = "monitoring"
      Role = "config-storage"
    }
}
