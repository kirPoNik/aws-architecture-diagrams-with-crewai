# Root Terragrunt configuration
# This file defines settings shared across all child modules

locals {
  # Load common tags from YAML file which is located relatively to root.hcl
  common_tags_file = yamldecode(file("${get_parent_terragrunt_dir()}/env.yaml"))

  # Convert to AWS tag format
  common_tags = {
    Environment = local.common_tags_file.environment
    Application = local.common_tags_file.application
    ManagedBy   = local.common_tags_file.managed_by
    CostCenter  = local.common_tags_file.cost_center
  }
  # AWS region
  aws_region = contains(keys(local.common_tags_file), "aws_region") ? local.common_tags_file.aws_region : "us-east-1"
}

# Generate provider block for all child modules
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "${local.aws_region}"

  default_tags {
    tags = ${jsonencode(local.common_tags)}
  }
}

terraform {
  required_version = ">= 1.0"
}
EOF
}

# Configure Terraform backend (local for this example)
# In production, you would use S3 backend
generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
terraform {
  backend "local" {}
}
EOF
}

# Input variables available to all modules
inputs = {
  common_tags = local.common_tags
}
