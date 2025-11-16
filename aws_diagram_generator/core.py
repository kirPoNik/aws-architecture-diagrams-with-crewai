"""Core processing logic for AWS architecture documentation generation."""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable CrewAI telemetry before importing crewai
os.environ['OTEL_SDK_DISABLED'] = 'true'

from crewai import Agent, Task, Crew, Process
from aws_diagram_generator.tools import AWSEnvironmentScannerTool
from aws_diagram_generator.bedrock_llm import BedrockLLM

logger = logging.getLogger(__name__)

# Constants
OUTPUT_DIR = Path("output")
DEFAULT_REGION = "us-east-1"
MAX_WORKERS = 3  # Parallel processing workers


def ensure_output_directory(target_name: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Create output directory structure for a target."""
    target_dir = output_dir / target_name.replace(' ', '_').lower()
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory created: {target_dir}")
    return target_dir


def save_output(target_name: str, content: str, filename: str, output_dir: Path = OUTPUT_DIR) -> None:
    """Save output to a file in the target's output directory."""
    try:
        target_output_dir = ensure_output_directory(target_name, output_dir)
        output_file = target_output_dir / filename

        with open(output_file, 'w') as f:
            f.write(content)

        logger.info(f"Saved output to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save output to {filename}: {e}")


def initialize_llm(model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
                   temperature: float = 0.1,
                   max_tokens: int = 16384,
                   region_name: str = "us-east-1") -> BedrockLLM:
    """Initialize the LLM using custom Bedrock wrapper.

    This bypasses LiteLLM to support AWS Bedrock inference profiles,
    which are required for newer models like Claude Sonnet 4.5.

    Args:
        model_id: Bedrock model ID or inference profile ID
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate
        region_name: AWS region

    Returns:
        BedrockLLM instance
    """
    try:
        llm = BedrockLLM(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            region_name=region_name
        )
        logger.info(f"LLM initialized with Bedrock: {model_id}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise


def process_target(target: Dict[str, Any], llm: BedrockLLM, output_dir: Path = OUTPUT_DIR) -> Dict[str, Any]:
    """Process a single target from the config."""
    target_name = target.get('name', 'Unknown Target')
    target_desc = f'"{target_name}" with tags: {target["tags"]}'

    logger.info(f"Processing Target: {target_name}")

    try:
        # Instantiate the custom tool for this target with its configuration
        aws_scanner_tool = AWSEnvironmentScannerTool(target_config=target)

        # Define the Agents
        inspector = Agent(
            role='AWS Infrastructure Inspector',
            goal='Scan the AWS environment for a specific application and provide a detailed JSON output of its resources.',
            backstory='You are an automated scanning agent that uses AWS APIs (Tagging and Config) to discover and list cloud resources based on predefined tags in a config file.',
            tools=[aws_scanner_tool],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        analyst = Agent(
            role='Cloud Architecture Analyst',
            goal='Analyze the provided JSON data to understand the cloud architecture, its components, and their relationships.',
            backstory='You are a senior cloud architect. Your expertise lies in interpreting raw infrastructure data and structuring it into a logical model that describes how different components are grouped and connected.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        draftsman = Agent(
            role='PlantUML Diagram Draftsman',
            goal='Generate a PlantUML diagram script based on the architectural analysis provided.',
            backstory='You are a technical diagramming expert specializing in PlantUML. You can convert structured architectural information into a clean, readable, and syntactically correct PlantUML script using the official AWS icon library.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        technical_writer = Agent(
            role='Technical Documentation Writer',
            goal='Generate a comprehensive technical runbook of the cloud architecture, tailored for engineers.',
            backstory='You are a meticulous technical writer who specializes in creating in-depth documentation for complex systems, focusing on details engineers need for operations and troubleshooting.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        executive_analyst = Agent(
            role='Executive Summary Analyst',
            goal='Summarize the cloud architecture into a high-level, non-technical executive summary.',
            backstory='A business analyst who excels at translating complex technical jargon into clear, concise language for C-level executives, focusing on business purpose and high-level posture.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        developer_advocate = Agent(
            role='Developer Relations Advocate',
            goal='Create a developer-focused README explaining how to interact with the application, its endpoints, and its data stores.',
            backstory='A DevRel advocate who knows exactly what developers need to get started, creating practical "how-to" guides that bridge the gap between infrastructure and application code.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        aggregator_agent = Agent(
            role='Documentation Aggregator',
            goal='Combine all generated documents (diagram, technical doc, executive summary, developer guide) into a single, unified report.',
            backstory='You are the chief editor, responsible for assembling all individual reports into a final, cohesive document.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        # Define the Tasks
        task_inspect = Task(
            description=f'Scan the AWS environment to get a complete inventory of the infrastructure components for the {target_desc} target. Use the available tool to perform the scan.',
            expected_output='A comprehensive JSON string detailing all discovered AWS resources related to the specified application environment.',
            agent=inspector
        )

        task_analyze = Task(
            description="""Analyze the JSON output from the infrastructure scan and create a detailed architectural analysis.

ANALYSIS REQUIREMENTS:

1. **Network Topology**:
   - Identify VPC ID, CIDR blocks, and region
   - List all availability zones in use
   - Map subnets to AZs (public vs private)
   - Note any NAT gateways, internet gateways, VPN connections

2. **Resource Categorization**:
   - **Compute Tier**: EC2 instances, Auto Scaling Groups, launch templates
   - **Load Balancing**: ALB/NLB/CLB, target groups, listeners
   - **Database Tier**: RDS instances, read replicas, Multi-AZ status
   - **Storage**: S3 buckets, EBS volumes, EFS file systems
   - **Caching**: ElastiCache, CloudFront distributions
   - **Security**: Security groups, NACLs, WAF rules
   - **IAM**: Roles, instance profiles, policies

3. **Resource Relationships** (CRITICAL FOR DIAGRAM):
   - Which subnet each resource is in
   - Which security groups apply to each resource
   - Load balancer → target group → instances mapping
   - Database connections (which instances connect to which DBs)
   - S3 bucket access patterns
   - IAM role attachments

4. **Traffic Flow Patterns**:
   - External traffic entry points (internet → ALB)
   - Inter-tier communication (web → app → database)
   - Outbound internet access (NAT gateway paths)
   - Cross-AZ traffic
   - CloudWatch/logging destinations

5. **Security Configuration**:
   - Security group rules (ingress/egress) with source/destination
   - NACL rules if present
   - Encryption settings
   - Public vs private subnets

EXPECTED OUTPUT FORMAT:
```
# Network Architecture
- VPC: vpc-xxx (10.0.0.0/16) in us-east-1
- AZ1: us-east-1a
  - Public Subnet: subnet-xxx (10.0.1.0/24)
  - Private Subnet: subnet-yyy (10.0.2.0/24)
- AZ2: us-east-1b
  - Public Subnet: subnet-zzz (10.0.3.0/24)

# Compute Resources
- EC2 Instance: i-xxx
  - Type: t3.medium
  - Subnet: subnet-xxx (Public, AZ us-east-1a)
  - Security Groups: sg-aaa (web-sg)
  - Private IP: 10.0.1.25
  - Public IP: 54.x.x.x

# Traffic Flows
1. Internet → ALB (sg-alb) on ports 80/443
2. ALB → Target Group → EC2 instances (sg-web) on port 80
3. EC2 instances (sg-web) → RDS (sg-db) on port 5432
4. EC2 instances → S3 bucket (via IAM role)
```

Be specific with actual IDs, IPs, and configurations from the scan data.""",
            expected_output='A comprehensive architectural analysis with network topology, resource categorization, detailed relationships, and traffic flows using ACTUAL resource IDs and configurations from the scan.',
            agent=analyst,
            context=[task_inspect]
        )

        task_draw = Task(
            description="""Based on the architectural analysis, create a detailed PlantUML script using the official AWS PlantUML library.

CRITICAL REQUIREMENTS:
1. **Use AWS PlantUML Icons**: Import from https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v18.0/dist
   - Example: !include AWSPuml/Compute/EC2.puml
   - Use proper AWS icon macros like EC2Instance(), RDSPostgreSQLInstance(), ElasticLoadBalancing()

2. **Proper Grouping Hierarchy** (VERY IMPORTANT):
   - Use AWSCloudGroup() for the AWS cloud boundary
   - Use VPCGroup() for VPC boundary
   - Use AvailabilityZoneGroup() for each AZ
   - Use PublicSubnetGroup() and PrivateSubnetGroup() for subnets
   - Resources go INSIDE their subnets, subnets INSIDE AZs, AZs INSIDE VPC

3. **Correct Component Placement**:
   - EC2 instances must be INSIDE subnet groups
   - RDS instances must be INSIDE private subnet groups
   - Load balancers must be INSIDE public subnet groups
   - S3 buckets are OUTSIDE VPC (separate rectangle)
   - CloudWatch and SNS are OUTSIDE VPC

4. **Traffic Flow Arrows**:
   - Internet -> ALB (ingress traffic)
   - ALB -> Target Group -> EC2 instances
   - EC2 -> RDS (database connections)
   - EC2 -> S3 (via IAM role)
   - Resources -> CloudWatch (metrics)
   - Use meaningful labels on arrows (e.g., "HTTPS:443", "PostgreSQL:5432")

5. **Security Groups**:
   - Show as dashed rectangles around resources
   - Include security group IDs and rules in notes

6. **Real Resource Information**:
   - Use ACTUAL resource IDs from the scan (not placeholders!)
   - Include instance types, IPs, database versions
   - Show Multi-AZ configuration if present

7. **Styling**:
   - Use skinparam linetype ortho for clean lines
   - Add legend with key information
   - Include notes for security groups and configuration

EXAMPLE STRUCTURE:
```
@startuml
!include AWSPuml/AWSCommon.puml
!include AWSPuml/Compute/EC2Instance.puml
!include AWSPuml/Database/RDSPostgreSQLInstance.puml

AWSCloudGroup(cloud) {
  VPCGroup(vpc, "VPC\\nvpc-xxx\\n10.0.0.0/16") {
    AvailabilityZoneGroup(az1, "us-east-1a") {
      PublicSubnetGroup(pub1, "Public Subnet") {
        EC2Instance(web1, "Web Server", "i-xxx\\nt3.medium")
      }
      PrivateSubnetGroup(priv1, "DB Subnet") {
        RDSPostgreSQLInstance(db, "PostgreSQL", "demo-db")
      }
    }
  }
}
web1 -down-> db : "PostgreSQL:5432"
@enduml
```

Generate a diagram that accurately reflects the ACTUAL discovered resources and their relationships.""",
            expected_output='A complete and syntactically correct PlantUML script that uses AWS icons, proper grouping hierarchy, real resource IDs, and accurate traffic flows. The script must start with @startuml and end with @enduml.',
            agent=draftsman,
            context=[task_analyze]
        )

        task_generate_technical_doc = Task(
            description='Analyze the JSON output from the inspector. Create a detailed, technical-level document in Markdown. This document should include a full list of discovered resources, their key configuration parameters (like instance types, subnet IDs), and a detailed breakdown of security group ingress/egress rules and network connectivity.',
            expected_output='A comprehensive Markdown document titled "Technical Infrastructure Runbook".',
            agent=technical_writer,
            context=[task_inspect]
        )

        task_generate_executive_summary = Task(
            description='Analyze the JSON output from the inspector. Write a one-page executive summary. The summary must be non-technical and focus on the business-level components (e.g., "Web Application," "Database") and their purpose. It should highlight the high-availability and security posture in simple terms.',
            expected_output='A short, non-technical executive summary in Markdown titled "Architecture Overview for Leadership".',
            agent=executive_analyst,
            context=[task_inspect]
        )

        task_generate_developer_readme = Task(
            description='Analyze the JSON output from the inspector. Create a "Developer Onboarding" section for a README file. This should identify the main application components (like load balancers and databases) and list their key connection details (e.g., "Connect to the database via this endpoint," "API is available at this load balancer DNS").',
            expected_output='A practical, developer-focused Markdown section titled "Developer Onboarding Guide".',
            agent=developer_advocate,
            context=[task_inspect]
        )

        task_aggregate = Task(
            description='Take the PlantUML script, the Technical Runbook, the Executive Summary, and the Developer Guide. Combine them into a single Markdown file with a table of contents.',
            expected_output='A single, combined Markdown file containing all artifacts, each under its own clear heading.',
            agent=aggregator_agent,
            context=[task_draw, task_generate_technical_doc, task_generate_executive_summary, task_generate_developer_readme]
        )

        # Assemble the Crew
        crew = Crew(
            agents=[
                inspector,
                analyst,
                draftsman,
                technical_writer,
                executive_analyst,
                developer_advocate,
                aggregator_agent
            ],
            tasks=[
                task_inspect,
                task_analyze,
                task_draw,
                task_generate_technical_doc,
                task_generate_executive_summary,
                task_generate_developer_readme,
                task_aggregate
            ],
            process=Process.sequential,
            verbose=True
        )

        # Kick off the process
        logger.info(f"Starting crew for target: {target_name}")
        result = crew.kickoff()

        # Save the aggregated output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"architecture_documentation_{timestamp}.md"
        save_output(target_name, str(result), output_filename, output_dir)

        logger.info(f"Successfully processed target: {target_name}")

        return {
            'target': target_name,
            'result': result,
            'status': 'success',
            'output_file': output_filename
        }

    except Exception as e:
        logger.error(f"Error processing target '{target_name}': {e}", exc_info=True)
        return {
            'target': target_name,
            'result': None,
            'status': 'failed',
            'error': str(e)
        }


def process_targets_parallel(targets: List[Dict[str, Any]], llm: BedrockLLM,
                            max_workers: int = MAX_WORKERS,
                            output_dir: Path = OUTPUT_DIR) -> List[Dict[str, Any]]:
    """Process multiple targets in parallel."""
    results = []

    logger.info(f"Processing {len(targets)} targets in parallel with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_target = {
            executor.submit(process_target, target, llm, output_dir): target
            for target in targets
        }

        # Collect results as they complete
        for future in as_completed(future_to_target):
            target = future_to_target[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Unexpected error in parallel processing for target '{target.get('name', 'Unknown')}': {e}")
                results.append({
                    'target': target.get('name', 'Unknown'),
                    'result': None,
                    'status': 'failed',
                    'error': str(e)
                })

    return results


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print a summary of all processed targets."""
    logger.info("=" * 80)
    logger.info("SUMMARY - All Targets Processed")
    logger.info("=" * 80)

    successful = 0
    failed = 0

    for i, result in enumerate(results, 1):
        status_symbol = "✓" if result['status'] == 'success' else "✗"
        logger.info(f"\n{i}. {status_symbol} {result['target']}")

        if result['status'] == 'success':
            successful += 1
            logger.info(f"   Output: {result.get('output_file', 'N/A')}")
        else:
            failed += 1
            logger.info(f"   Error: {result.get('error', 'Unknown error')}")

    logger.info("\n" + "=" * 80)
    logger.info(f"Total: {len(results)} | Successful: {successful} | Failed: {failed}")
    logger.info("=" * 80)
