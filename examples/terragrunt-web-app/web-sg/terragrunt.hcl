# Web Security Group - Pure Terragrunt Configuration
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
    vpc_id = "vpc-fake-id"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

terraform {
  source = "tfr:///terraform-aws-modules/security-group/aws?version=5.2.0"
}

inputs = {
  name        = "web-app-web-sg"
  description = "Security group for web servers"
  vpc_id      = dependency.vpc.outputs.vpc_id

  # Ingress rules
  ingress_with_cidr_blocks = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "HTTP from internet"
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "HTTPS from internet"
    },
    {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "SSH access"
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
      Tier = "application"
    }
  )
}
