# AWS Config Configuration Recorder and Delivery Channel

variable "s3_bucket_id" {
  description = "S3 bucket ID for AWS Config delivery channel"
  type        = string
}

variable "tags" {
  description = "Tags to apply to AWS Config resources"
  type        = map(string)
  default     = {}
}

# IAM Role for AWS Config
resource "aws_iam_role" "config" {
  name = "aws-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Attach AWS managed policy for Config
resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

# Additional policy for S3 access
resource "aws_iam_role_policy" "config_s3" {
  name = "aws-config-s3-policy"
  role = aws_iam_role.config.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketVersioning",
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_id}",
          "arn:aws:s3:::${var.s3_bucket_id}/*"
        ]
      }
    ]
  })
}

# AWS Config Recorder
resource "aws_config_configuration_recorder" "main" {
  name     = "web-app-config-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }

  # Ensure IAM policies are attached before creating recorder
  depends_on = [
    aws_iam_role_policy_attachment.config,
    aws_iam_role_policy.config_s3
  ]
}

# AWS Config Delivery Channel
resource "aws_config_delivery_channel" "main" {
  name           = "web-app-config-delivery"
  s3_bucket_name = var.s3_bucket_id

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on = [aws_config_configuration_recorder.main]
}

# Start the Config Recorder
resource "aws_config_configuration_recorder_status" "main" {
  name       = aws_config_configuration_recorder.main.name
  is_enabled = true

  depends_on = [aws_config_delivery_channel.main]
}

# Outputs
output "config_recorder_id" {
  description = "The ID of the AWS Config Recorder"
  value       = aws_config_configuration_recorder.main.id
}

output "config_recorder_role_arn" {
  description = "The ARN of the IAM role used by AWS Config"
  value       = aws_iam_role.config.arn
}
