# RDS Database - Pure Terragrunt Configuration
# Directly uses terraform-aws-modules/rds/aws

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
    private_subnets = ["subnet-fake-1", "subnet-fake-2"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

dependency "db_sg" {
  config_path = "../db-sg"

  mock_outputs = {
    security_group_id = "sg-fake-id"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

terraform {
  source = "tfr:///terraform-aws-modules/rds/aws?version=6.10.0"
}

inputs = {
  identifier = "web-app-db"

  engine               = "postgres"
  engine_version       = "16.3"
  family               = "postgres16"
  major_engine_version = "16"
  instance_class       = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 40
  storage_encrypted     = true

  db_name  = "webapp"
  username = "dbadmin"
  password = "ChangeMe123!Demo"  # IMPORTANT: Use AWS Secrets Manager in production!
  port     = 5432

  multi_az                = false  # Single AZ for demo/cost savings
  create_db_subnet_group  = true
  db_subnet_group_name    = "web-app-db-subnet-group-${get_aws_account_id()}"
  subnet_ids              = dependency.vpc.outputs.private_subnets
  vpc_security_group_ids  = [dependency.db_sg.outputs.security_group_id]

  # Backups
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  # Enhanced monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  create_cloudwatch_log_group     = true

  # Disable deletion protection for demo
  deletion_protection = false
  skip_final_snapshot = true

  tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "data"
      Role = "database"
    }
  )
}
