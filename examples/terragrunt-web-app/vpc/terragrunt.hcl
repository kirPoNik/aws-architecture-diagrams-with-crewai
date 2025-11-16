# VPC Module - Pure Terragrunt Configuration
# Directly uses terraform-aws-modules/vpc/aws from Terraform Registry

include "root" {
  path   = find_in_parent_folders("root.hcl")
  expose = true
}

dependency "aws_config" {
  config_path = "../aws-config"
  skip_outputs = true
}

terraform {
  source = "tfr:///terraform-aws-modules/vpc/aws?version=5.13.0"
}

inputs = {
  name = "${include.root.locals.common_tags["Application"]}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.11.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true  # Cost optimization for demo
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Additional tags for VPC-specific resources
  tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "network"
    }
  )

  public_subnet_tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "network"
      Type = "public"
    }
  )

  private_subnet_tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "network"
      Type = "private"
    }
  )

  nat_gateway_tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "network"
    }
  )

  igw_tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "network"
    }
  )
}
