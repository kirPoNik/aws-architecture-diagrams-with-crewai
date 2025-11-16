# Quick Start Guide

Get up and running with AWS Architecture Diagrams Generator in 5 minutes.

## Prerequisites

- Python 3.8+
- AWS credentials configured
- AWS Config enabled in your target region
- AWS Bedrock access with Claude 3.5 Sonnet enabled

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd aws-architecture-diagrams-with-crewai

# Install the package
pip install -e .
```

## Quick Test

### Option 1: Using CLI Arguments (Fastest)

```bash
aws-diagram-generator \
  --name "My Environment" \
  --region us-east-1 \
  --tags "Environment=production"
```

### Option 2: Using a Config File

1. Create `config.yaml`:
```yaml
targets:
  - name: "Production"
    region: "us-east-1"
    tags:
      - Key: "Environment"
        Value: "production"
```

2. Run the generator:
```bash
aws-diagram-generator --config config.yaml
```

## What Happens

1. The tool scans AWS for resources with your specified tags
2. AI agents analyze the infrastructure
3. Documentation is generated and saved to `output/<target-name>/`

## Output

Check the `output/` directory for your generated documentation:

```bash
ls -la output/my_environment/
```

You'll find a Markdown file with:
- PlantUML architecture diagram
- Technical runbook
- Executive summary
- Developer guide

## Next Steps

- Customize the configuration for multiple environments
- Adjust LLM parameters for different output styles
- Use `--verbose` flag to see detailed processing logs
- Process multiple targets in parallel with `--max-workers`

## Common Issues

### "No resources found"
- Verify tags exist on your AWS resources
- Check you're scanning the correct region
- Ensure tag keys and values match exactly (case-sensitive)

### "AWS Config not enabled"
- Enable AWS Config in the AWS Console
- Wait 10-15 minutes for initial resource discovery

### "Bedrock access denied"
- Request access to Claude 3.5 Sonnet in Bedrock console
- Verify IAM permissions include `bedrock:InvokeModel`

## Examples

### Generate docs for multiple environments
```bash
# Create config.yaml with multiple targets
aws-diagram-generator --config config.yaml --max-workers 3
```

### Custom output directory
```bash
aws-diagram-generator \
  --name "Staging" \
  --region us-west-2 \
  --tags "Environment=staging" \
  --output ./staging-docs
```

### Verbose logging
```bash
aws-diagram-generator --config config.yaml --verbose
```

## Help

```bash
aws-diagram-generator --help
```

For more details, see the full [README.md](README.md).
