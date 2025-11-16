# AWS Architecture Diagrams with CrewAI

Automatically generate comprehensive AWS architecture documentation including PlantUML diagrams, technical runbooks, executive summaries, and developer guides using AI agents powered by CrewAI and AWS Bedrock Claude Sonnet 4.5.

**Now supports AWS Bedrock inference profiles for the latest Claude models!**

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[README](README.md)** - Full documentation (this file)

## Features

- **Automated AWS Resource Discovery**: Scans AWS environments using Resource Groups Tagging API and AWS Config
- **Multi-Agent AI System**: Utilizes 7 specialized AI agents for different documentation tasks
- **Comprehensive Documentation**: Generates PlantUML diagrams, technical runbooks, executive summaries, and developer guides
- **Parallel Processing**: Efficiently processes multiple targets concurrently
- **Batch API Optimization**: Uses AWS Config batch APIs to minimize API calls and avoid rate limits
- **Robust Error Handling**: Comprehensive logging and error recovery mechanisms
- **File Output Management**: Organized output directory structure with timestamped files

## Architecture

The system uses a multi-agent approach with the following specialized agents:

1. **AWS Infrastructure Inspector**: Scans AWS environment and collects resource data
2. **Cloud Architecture Analyst**: Analyzes infrastructure relationships and tiers
3. **PlantUML Diagram Draftsman**: Generates PlantUML architecture diagrams
4. **Technical Documentation Writer**: Creates detailed technical runbooks
5. **Executive Summary Analyst**: Produces high-level executive summaries
6. **Developer Relations Advocate**: Writes developer onboarding guides
7. **Documentation Aggregator**: Combines all outputs into unified documentation

## Prerequisites

### AWS Requirements

1. **AWS Config** must be enabled in your AWS account and region
   - AWS Config records resource configurations and changes
   - Without AWS Config, resource details cannot be retrieved

2. **AWS Bedrock** access with Claude Sonnet 4.5 (or other supported models)
   - **Recommended:** Claude Sonnet 4.5 via inference profile: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
   - **Alternative:** Claude 3.5 Sonnet: `anthropic.claude-3-5-sonnet-20240620-v1:0`
   - **Alternative:** Amazon Nova Premier: `us.amazon.nova-premier-v1:0`
   - **Alternative:** Meta Llama 3.3 70B: `meta.llama3-3-70b-instruct-v1:0`
   - Must have model access enabled in AWS Bedrock console
   - For Anthropic models: Submit use case form (one-time, 5-15 min approval)

3. **AWS Credentials** configured via one of:
   - AWS CLI (`aws configure`)
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - IAM role (if running on EC2/ECS/Lambda)
   - AWS SSO profile

### Required IAM Permissions

Create an IAM policy with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "tag:GetResources",
        "tag:GetTagKeys",
        "tag:GetTagValues"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "config:SelectResourceConfig",
        "config:BatchGetResourceConfig",
        "config:GetResourceConfigHistory",
        "config:ListDiscoveredResources"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.*",
        "arn:aws:bedrock:*::foundation-model/amazon.*",
        "arn:aws:bedrock:*::foundation-model/meta.*"
      ]
    }
  ]
}
```

**Note**: These permissions are read-only and follow the principle of least privilege.

### Python Requirements

- Python 3.8 or higher
- pip package manager

## Installation

### Option 1: Install as a Package (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd aws-architecture-diagrams-with-crewai
   ```

2. **Install the package**:
   ```bash
   # Install in development mode (editable)
   pip install -e .

   # Or install normally
   pip install .
   ```

   This installs the package and creates command-line tools:
   - `aws-diagram-generator`
   - `aws-diagrams` (alias)

### Option 2: Install from PyPI (when published)

```bash
pip install aws-architecture-diagrams
```

### Option 3: Development Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd aws-architecture-diagrams-with-crewai
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (optional):
   Create a `.env` file for environment-specific settings:
   ```bash
   AWS_PROFILE=your-profile-name
   AWS_REGION=us-east-1
   ```

## Configuration

Edit `config.yaml` to define your target environments:

```yaml
targets:
  - name: "Production Environment"
    region: "us-east-1"
    tags:
      - Key: "Environment"
        Value: "production"
      - Key: "Application"
        Value: "my-app"

  - name: "Development Environment"
    region: "us-west-2"
    tags:
      - Key: "Environment"
        Value: "development"
      - Key: "Application"
        Value: "my-app"
```

### Configuration Fields

- `name` (required): Friendly name for the target environment
- `region` (required): AWS region to scan
- `tags` (required): List of tags to filter resources
  - `Key`: Tag key name
  - `Value`: Tag value to match

**Note**: Resources must match ALL specified tags (AND logic).

## Usage

### Using the Command-Line Tool

After installing the package, you can use the `aws-diagram-generator` command:

#### Option 1: Using a Configuration File

```bash
# Use default config.yaml
aws-diagram-generator --config config.yaml

# Specify custom configuration file
aws-diagram-generator --config /path/to/my-config.yaml

# With custom output directory
aws-diagram-generator --config config.yaml --output ./documentation
```

#### Option 2: Using Command-Line Arguments

Generate documentation for a single target without a config file:

```bash
# Basic usage with name, region, and tags
aws-diagram-generator \
  --name "Production Environment" \
  --region us-east-1 \
  --tags "Environment=production" "Application=myapp"

# With multiple tags
aws-diagram-generator \
  --name "Staging" \
  --region us-west-2 \
  --tags "Environment=staging" "Team=platform" "CostCenter=engineering"

# Specify output directory
aws-diagram-generator \
  --name "Production" \
  --region us-east-1 \
  --tags "Environment=prod" \
  --output ./prod-docs
```

#### Advanced Options

```bash
# Enable verbose logging
aws-diagram-generator --config config.yaml --verbose

# Custom log file
aws-diagram-generator --config config.yaml --log-file my-custom.log

# Adjust parallel workers (for multiple targets in config)
aws-diagram-generator --config config.yaml --max-workers 5

# Use different model (default is Claude Sonnet 4.5)
aws-diagram-generator \
  --config config.yaml \
  --model-id "us.amazon.nova-premier-v1:0" \
  --temperature 0.2 \
  --max-tokens 16384

# Get help
aws-diagram-generator --help

# Check version
aws-diagram-generator --version
```

### Using as a Python Module

```python
from aws_diagram_generator import initialize_llm, process_target
from aws_diagram_generator.config import create_target_from_cli

# Create a target
target = create_target_from_cli(
    name="My Environment",
    region="us-east-1",
    tags=["Environment=production", "App=myapp"]
)

# Initialize LLM
llm = initialize_llm()

# Process the target
result = process_target(target, llm)

print(f"Status: {result['status']}")
print(f"Output: {result['output_file']}")
```

### Legacy Usage (Direct Script Execution)

If you haven't installed the package, you can still run the script directly:

```bash
python main.py --config config.yaml
```

### Output

The script creates an `output/` directory with subdirectories for each target:

```
output/
├── production_environment/
│   └── architecture_documentation_20250108_143022.md
└── development_environment/
    └── architecture_documentation_20250108_143045.md
```

Each documentation file contains:
- Table of Contents
- PlantUML Architecture Diagram
- Technical Infrastructure Runbook
- Executive Summary
- Developer Onboarding Guide

### Logs

Logs are written to:
- Console (stdout)
- `aws_diagram_generator.log` file

Log levels can be adjusted in `main.py` by modifying the `logging.basicConfig()` call.

## Parallel Processing

The system automatically processes multiple targets in parallel:

- **Single target**: Processes directly (no parallelization overhead)
- **Multiple targets**: Uses ThreadPoolExecutor with configurable workers

Adjust the number of parallel workers using the CLI:

```bash
# Process with 5 parallel workers
aws-diagram-generator --config config.yaml --max-workers 5
```

Or programmatically:

```python
from aws_diagram_generator import process_targets_parallel, initialize_llm

llm = initialize_llm()
results = process_targets_parallel(targets, llm, max_workers=5)
```

**Note**: Consider AWS API rate limits when increasing parallelism. Default is 3 workers.

### Common Issues

#### AWS Config Not Enabled

**Error**: `No config found for <resource-arn>`

**Solution**: Enable AWS Config in your target region:
1. Go to AWS Config console
2. Click "Get started"
3. Follow the setup wizard
4. Wait 10-15 minutes for initial discovery

#### Model Access Required

**Error**: `Model use case details have not been submitted`

**Solution** (for Anthropic Claude models):
1. Go to AWS Bedrock Console → Model access
2. Click "Manage model access"
3. Find Anthropic section → Submit use case details
4. Fill out form
5. Wait 5-15 minutes for approval

#### Inference Profile Required

**Error**: `Invocation of model ID ... with on-demand throughput isn't supported`

**Solution**: Use inference profile format with `us.` prefix:
- Wrong: `anthropic.claude-sonnet-4-5-20250929-v1:0`
- Correct: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`

#### Read Timeout

**Error**: `ReadTimeoutError: Read timeout on endpoint URL`

**Solution**: Already fixed with 15-minute timeout in BedrockLLM. If still occurring:
```bash
aws-diagram-generator --max-tokens 8192 --config config.yaml
```

#### Throttling

**Error**: `ThrottlingException: Too many requests`

**Solution**: Use inference profiles (higher quotas) or wait and retry

### No Resources Found

**Error**: `No resources found matching the specified tags`

**Solutions**:
- Verify tags exist on your resources in the AWS console
- Check that tag keys and values match exactly (case-sensitive)
- Ensure you're scanning the correct region
- Verify resources are tagged with ALL specified tags

### Rate Limiting

**Error**: `ThrottlingException` or `Rate exceeded`

**Solution**:
- The tool includes automatic retry logic with exponential backoff
- Reduce `MAX_WORKERS` to decrease API call rate
- Increase the `sleep()` delay in `aws_inspector_tools.py`

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'langchain_aws'`

**Solution**:
```bash
pip install -r requirements.txt
```

Ensure `langchain-aws` is uncommented in `requirements.txt`.

## Advanced Configuration

### Custom Model Settings

The tool now uses a custom `BedrockLLM` wrapper that supports AWS Bedrock inference profiles:

```python
from aws_diagram_generator import initialize_llm

# Initialize with Claude Sonnet 4.5 (default)
llm = initialize_llm(
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    temperature=0.1,      # Lower = more deterministic
    max_tokens=16384,     # Maximum response length
    region_name="us-east-1"
)

# Or use Amazon Nova Premier
llm = initialize_llm(
    model_id="us.amazon.nova-premier-v1:0",
    temperature=0.2,
    max_tokens=32000
)
```

**Key Features:**
- Supports AWS Bedrock inference profiles (required for Claude 4.x, Nova Premier)
- Extended timeout (15 minutes) to prevent timeout errors
- Automatic retries with adaptive backoff
- Compatible with CrewAI agents


### Batch Size Tuning

Adjust AWS Config batch size in `tools/aws_inspector_tools.py`:

```python
def _batch_hydrate_configurations(
    self,
    resources: List[Dict[str, Any]],
    config_client,
    batch_size: int = 20  # Increase for faster processing
) -> None:
```

**Note**: Larger batch sizes = faster but higher risk of rate limiting.

## Cost Considerations

### AWS Costs

1. **AWS Config**: Charged per configuration item recorded
2. **AWS Bedrock**: Charged per input/output token
3. **Data Transfer**: Minimal (API calls only)

### Cost Optimization

- Process fewer targets at once
- Use specific tags to limit resource scope
- Run during off-peak hours if using shared AWS accounts

## Development

### Project Structure

```
.
├── main.py                    # Main orchestration script
├── config.yaml                # Target configuration
├── requirements.txt           # Python dependencies
├── tools/
│   └── aws_inspector_tools.py # AWS scanning tool
├── output/                    # Generated documentation
└── aws_diagram_generator.log  # Application logs
```

### Testing

Test the AWS scanner tool independently:

```bash
python test.py
```

This validates AWS credentials and Config access without running the full AI pipeline.

### Adding Resource Type Support

Extend the resource type mapping in `tools/aws_inspector_tools.py`:

```python
def _map_service_to_config_type(self, service: str, resource_type: str) -> str:
    mapping = {
        ('ec2', 'instance'): 'AWS::EC2::Instance',
        ('myservice', 'myresource'): 'AWS::MyService::MyResource',  # Add here
        # ...
    }
```

## Limitations

1. **AWS Config Dependency**: Requires AWS Config to be enabled
2. **Region-Specific**: Scans one region per target
3. **Tag-Based Only**: Currently only supports tag-based resource discovery
4. **Rate Limits**: Subject to AWS API throttling limits
5. **Model Context**: Large infrastructures may exceed token limits

## Contributing

Contributions are welcome! Areas for improvement:

- Support for VPC-based scanning
- Multi-region aggregation
- Additional output formats (PDF, HTML)
- Resource relationship graph generation
- Cost estimation integration

## License

[Specify your license here]

## Support

For issues and questions:
- Check the Troubleshooting section above
- Review logs in `aws_diagram_generator.log`
- Verify AWS Config and Bedrock setup
- Ensure IAM permissions are correctly configured

## Acknowledgments

- Built with [CrewAI](https://github.com/joaomdmoura/crewAI)
- Powered by AWS Bedrock Claude 3.5 Sonnet
- Uses AWS Resource Groups Tagging API and AWS Config
