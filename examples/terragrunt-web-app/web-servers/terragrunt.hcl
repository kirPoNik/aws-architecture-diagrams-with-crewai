# Web Servers (EC2) - Pure Terragrunt Configuration
# Directly uses terraform-aws-modules/ec2-instance/aws

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
    public_subnets = ["subnet-fake-1", "subnet-fake-2"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

dependency "web_sg" {
  config_path = "../web-sg"

  mock_outputs = {
    security_group_id = "sg-fake-id"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

terraform {
  source = "tfr:///terraform-aws-modules/ec2-instance/aws?version=6.1.4"
}

# Get latest Amazon Linux 2023 AMI
locals {
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Web Server - web-app</h1>" > /var/www/html/index.html
              EOF
}

inputs = {
  name = "web-app-web-1"

  ami                    = "ami-0453ec754f44f9a4a"  # Amazon Linux 2023 us-east-1
  instance_type          = "t3.micro"
  subnet_id              = dependency.vpc.outputs.public_subnets[0]
  vpc_security_group_ids = [dependency.web_sg.outputs.security_group_id]

  user_data_base64            = base64encode(local.user_data)
  user_data_replace_on_change = true

  enable_volume_tags = false
  root_block_device = {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
    tags = merge(
      include.root.locals.common_tags,
      {
        Name = "web-app-web-1-root"
        Tier = "application"
      }
    )
  }

  tags = merge(
    include.root.locals.common_tags,
    {
      Tier = "application"
      Role = "web-server"
    }
  )
}
