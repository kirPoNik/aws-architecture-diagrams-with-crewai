# AWS Config - Custom Terraform Configuration
# Enables AWS Config for infrastructure discovery and compliance tracking

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "s3_config" {
  config_path = "../aws-config-bucket"

  mock_outputs = {
    s3_bucket_id  = "fake-config-bucket"
    s3_bucket_arn = "arn:aws:s3:::fake-config-bucket"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

terraform {
  source = "${get_terragrunt_dir()}/."
}

inputs = {
  # Use dedicated AWS Config S3 bucket for Config snapshots
  s3_bucket_id = dependency.s3_config.outputs.s3_bucket_id

  tags  = {
      Name = "aws-config"
      Tier = "monitoring"
      Role = "config-recorder"
    }
}