# Database Security Group - Pure Terragrunt Configuration
# Directly uses terraform-aws-modules/security-group/aws

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "aws_config" {
  config_path = "../aws-config"
  skip_outputs = true
}

dependency "vpc" {
  config_path = "../vpc"

  mock_outputs = {
    vpc_id         = "vpc-fake-id"
    vpc_cidr_block = "10.0.0.0/16"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

terraform {
  source = "tfr:///terraform-aws-modules/security-group/aws?version=5.2.0"
}

inputs = {
  name        = "web-app-rds-sg"
  description = "Security group for RDS PostgreSQL database"
  vpc_id      = dependency.vpc.outputs.vpc_id

  # Ingress rule for PostgreSQL
  ingress_with_cidr_blocks = [
    {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = dependency.vpc.outputs.vpc_cidr_block
      description = "PostgreSQL from VPC"
    }
  ]

  # Egress rules
  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = "0.0.0.0/0"
      description = "Allow all outbound"
    }
  ]

  tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "data"
    }
  )
}
