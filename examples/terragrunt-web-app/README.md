# Terragrunt Web Application Example

This example demonstrates how to use **pure Terragrunt** configuration to create AWS infrastructure with consistent tags that can be scanned by the aws_diagram_generator.

**No custom Terraform code** - only `terragrunt.hcl` files that reference public Terraform modules!

## Architecture Overview

This example creates a simple 3-tier web application infrastructure using **official Terraform modules** from the Terraform Registry:

- **VPC**: Network with public and private subnets (`terraform-aws-modules/vpc/aws`)
- **Security Groups**: Web and database security groups (`terraform-aws-modules/security-group/aws`)
- **EC2**: Web server instances (`terraform-aws-modules/ec2-instance/aws`)
- **RDS**: PostgreSQL database (`terraform-aws-modules/rds/aws`)
- **S3**: Static content and logs storage (`terraform-aws-modules/s3-bucket/aws`)

All resources are tagged consistently via Terragrunt's `default_tags` to enable automated documentation generation.

## Pure Terragrunt Approach

This example uses **pure Terragrunt** - there are NO `.tf` files in this repository. Each module directory contains only a single `terragrunt.hcl` file that:

1. References a public Terraform module from the Terraform Registry
2. Configures the module inputs
3. Manages dependencies between modules
4. Inherits common tags from the root configuration

This is the recommended Terragrunt pattern for:
- **Consistency**: Use battle-tested public modules
- **Maintainability**: No custom Terraform code to maintain
- **Simplicity**: Pure configuration, no infrastructure code

## Prerequisites

1. **Terragrunt** installed (v0.45.0 or later)
2. **Terraform** installed (v1.0.0 or later)
3. **AWS CLI** configured with appropriate credentials
4. **AWS Config** enabled in your target region
5. **IAM permissions** for creating EC2, VPC, RDS, and S3 resources

## Directory Structure

```
terragrunt-web-app/
├── README.md                    # This file
├── config.yaml                  # aws_diagram_generator configuration
├── terragrunt.hcl              # Root Terragrunt configuration
├── deploy.sh                    # Quick deployment script
├── destroy.sh                   # Cleanup script
├── common/
│   └── tags.yaml               # Common tags for all resources
├── vpc/
│   └── terragrunt.hcl          # VPC module (terraform-aws-modules/vpc/aws)
├── web-sg/
│   └── terragrunt.hcl          # Web security group
├── web-servers/
│   └── terragrunt.hcl          # EC2 web servers
├── db-sg/
│   └── terragrunt.hcl          # Database security group
├── database/
│   └── terragrunt.hcl          # RDS PostgreSQL
├── s3-static/
│   └── terragrunt.hcl          # S3 static content bucket
└── s3-logs/
    └── terragrunt.hcl          # S3 logs bucket
```

**Note**: Each directory contains ONLY a `terragrunt.hcl` file - no `.tf` files!

## Tagging Strategy

All resources are tagged via the root `terragrunt.hcl` using AWS provider's `default_tags`:

- **Environment**: `demo` - Identifies the environment
- **Application**: `web-app` - Application identifier
- **ManagedBy**: `terragrunt` - Indicates infrastructure as code tool
- **CostCenter**: `engineering` - For cost allocation

These tags are used by aws_diagram_generator to discover and document resources.

## Quick Start

### Option 1: Automated Deployment

```bash
# Navigate to the example directory
cd aws_diagram_generator/examples/terragrunt-web-app

# Run the deployment script
./deploy.sh
```

### Option 2: Manual Deployment

```bash
# Deploy modules in order
cd vpc && terragrunt apply && cd ..
cd web-sg && terragrunt apply && cd ..
cd web-servers && terragrunt apply && cd ..
cd db-sg && terragrunt apply && cd ..
cd database && terragrunt apply && cd ..
cd s3-static && terragrunt apply && cd ..
cd s3-logs && terragrunt apply && cd ..
```

### Option 3: Terragrunt Run-All (Advanced)

```bash
# Deploy all modules in parallel (Terragrunt handles dependencies)
terragrunt run-all apply
```

### 2. Wait for AWS Config

After deploying resources, wait 10-15 minutes for AWS Config to discover and record the new resources.

### 3. Generate Documentation

```bash
# From the project root (uses Claude Sonnet 4.5 by default)
aws-diagram-generator --config examples/terragrunt-web-app/aws_diagram_generator_config.yaml

# Or with custom output directory
aws-diagram-generator \
  --config examples/terragrunt-web-app/aws_diagram_generator_config.yaml \
  --output ./my-docs

# Use a different model (e.g., Amazon Nova Premier)
aws-diagram-generator \
  --model-id us.amazon.nova-premier-v1:0 \
  --config examples/terragrunt-web-app/aws_diagram_generator_config.yaml

# Adjust output length for large infrastructures
aws-diagram-generator \
  --max-tokens 32000 \
  --config examples/terragrunt-web-app/aws_diagram_generator_config.yaml
```

**Available Models:**
- **Claude Sonnet 4.5** (default): `us.anthropic.claude-sonnet-4-5-20250929-v1:0` - Best for PlantUML diagrams
- **Amazon Nova Premier**: `us.amazon.nova-premier-v1:0` - Amazon's most capable model
- **Meta Llama 3.3 70B**: `meta.llama3-3-70b-instruct-v1:0` - Good alternative

**Note:** Anthropic models require submitting a use case form (see main README).

This will:
1. Scan AWS resources with matching tags
2. Generate architecture diagrams
3. Create technical documentation
4. Produce executive summaries

### 4. View Output

Documentation will be generated in:
```
output/demo_web_application/architecture_documentation_YYYYMMDD_HHMMSS.md
```

## Customization

### Change Tags

Edit `common/tags.yaml` to modify the tagging strategy:

```yaml
environment: "staging"  # Change to staging, production, etc.
application: "my-app"   # Change to your app name
```

After changing tags, also update `config.yaml` to match:

```yaml
targets:
  - name: "My Application"
    region: "us-east-1"
    tags:
      - Key: "Environment"
        Value: "staging"
      - Key: "Application"
        Value: "my-app"
```

### Use Different Terraform Modules

Simply edit the `terragrunt.hcl` file in any module directory and change the `source`:

```hcl
terraform {
  source = "tfr:///your-org/your-module/aws?version=1.0.0"
}
```

### Add More Resources

1. Create a new directory (e.g., `alb/`)
2. Add a `terragrunt.hcl` file referencing a public module
3. Configure dependencies if needed
4. Apply the module

Example:
```bash
mkdir alb
cat > alb/terragrunt.hcl <<EOF
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "tfr:///terraform-aws-modules/alb/aws?version=9.0.0"
}

inputs = {
  # Your ALB configuration here
}
EOF

cd alb && terragrunt apply
```

### Change AWS Region

Edit the root `terragrunt.hcl`:

```hcl
locals {
  aws_region = "us-west-2"  # Change region
}
```

Also update `config.yaml`:

```yaml
targets:
  - name: "Demo Web Application"
    region: "us-west-2"  # Match the region
```

## Cost Considerations

This example creates billable AWS resources:

- **VPC**: Free (up to limits)
- **NAT Gateway**: ~$32/month (can disable for dev)
- **EC2**: t3.micro instance (~$7.50/month)
- **RDS**: db.t3.micro (~$15/month)
- **S3**: Pay per storage and requests (~$1-5/month)

**Estimated cost**: ~$55-60/month if left running

### Cost Optimization Tips

1. **Disable NAT Gateway for dev**: Edit `vpc/terragrunt.hcl` set `enable_nat_gateway = false`
2. **Use smaller instance**: Change instance types in module configs
3. **Reduce RDS backup retention**: Edit `database/terragrunt.hcl`

### Clean Up

To avoid charges, destroy resources when done:

```bash
# Automated cleanup
./destroy.sh

# Or manual cleanup (reverse order)
cd s3-logs && terragrunt destroy && cd ..
cd s3-static && terragrunt destroy && cd ..
cd database && terragrunt destroy && cd ..
cd db-sg && terragrunt destroy && cd ..
cd web-servers && terragrunt destroy && cd ..
cd web-sg && terragrunt destroy && cd ..
cd vpc && terragrunt destroy && cd ..
```

## Troubleshooting

### Resources Not Found by Generator

**Issue**: aws_diagram_generator reports "No resources found"

**Solutions**:
1. Verify tags exist on resources in AWS Console
2. Check that AWS Config is enabled and has completed initial scan
3. Ensure all tag keys and values match exactly (case-sensitive)
4. Wait 15-20 minutes after resource creation for Config to index

### Terragrunt Dependency Errors

**Issue**: Resources fail to create due to missing dependencies

**Solution**: Deploy modules in order using `./deploy.sh` or manually:
1. VPC first (no dependencies)
2. Security groups (depend on VPC)
3. EC2, RDS, S3 (depend on VPC and security groups)

### Module Not Found

**Issue**: `Error downloading modules: module not found`

**Solution**: Check internet connectivity and Terraform Registry access. The `tfr:///` prefix requires Terragrunt to download from Terraform Registry.

### AWS Config Not Enabled

**Issue**: Generator fails with "No config found"

**Solution**:
1. Go to AWS Config console
2. Enable AWS Config in your target region
3. Wait for initial resource discovery (10-15 minutes)

## Advanced Usage

### Multiple Environments

Create separate configurations for each environment:

```bash
# Copy the example
cp -r terragrunt-web-app terragrunt-web-app-prod

# Edit common/tags.yaml
environment: "production"

# Update config.yaml with production tags
```

### Custom Module Versions

Pin specific module versions in each `terragrunt.hcl`:

```hcl
terraform {
  source = "tfr:///terraform-aws-modules/vpc/aws?version=5.13.0"  # Exact version
}
```

### Using Private Modules

Reference private modules or Git repositories:

```hcl
terraform {
  # GitHub repository
  source = "git::https://github.com/your-org/terraform-modules.git//vpc?ref=v1.0.0"

  # Or Terraform Cloud/Enterprise
  source = "app.terraform.io/your-org/vpc/aws"
}
```

### Dependency Management

Terragrunt automatically handles dependencies via `dependency` blocks:

```hcl
dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  vpc_id = dependency.vpc.outputs.vpc_id
}
```

## Benefits of Pure Terragrunt

This example demonstrates the benefits of pure Terragrunt configuration:

1. **No Custom Code**: Zero `.tf` files to maintain
2. **Battle-Tested Modules**: Uses well-maintained public modules
3. **Easy Updates**: Bump module versions to get new features
4. **Consistent Patterns**: Every module follows the same structure
5. **Reduced Complexity**: Pure configuration, no infrastructure code
6. **Better Testing**: Public modules are tested by the community
7. **Auto-Documentation**: aws_diagram_generator scans live resources, not code

## Next Steps

1. **Explore Generated Documentation**: Review the diagrams and technical documentation
2. **Add More Components**: Try adding ALB, CloudFront, or Lambda modules
3. **Integrate into CI/CD**: Automate documentation generation on infrastructure changes
4. **Create Multiple Environments**: Use this as a template for dev/staging/prod
5. **Customize Modules**: Fork public modules for organization-specific needs

## Support

For issues with:
- **Terragrunt**: See https://terragrunt.gruntwork.io/docs/
- **Terraform Modules**: Check module documentation on Terraform Registry
- **AWS Resources**: Review AWS service documentation
- **aws_diagram_generator**: See main project README and troubleshooting guide

## Learn More

- **Terraform Module Registry**: https://registry.terraform.io/browse/modules
- **Terragrunt Documentation**: https://terragrunt.gruntwork.io/
- **AWS Config**: https://aws.amazon.com/config/
- **Tagging Best Practices**: https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html
