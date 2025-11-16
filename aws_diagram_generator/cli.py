"""Command-line interface for AWS architecture diagram generator."""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Disable CrewAI telemetry
os.environ['OTEL_SDK_DISABLED'] = 'true'

from aws_diagram_generator.config import load_config, create_target_from_cli
from aws_diagram_generator.core import (
    initialize_llm,
    process_target,
    process_targets_parallel,
    print_summary,
    OUTPUT_DIR,
    MAX_WORKERS,
)
from aws_diagram_generator import __version__


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging based on CLI arguments."""
    log_level = logging.DEBUG if verbose else logging.INFO

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate AWS architecture documentation using AI agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use configuration file
  aws-diagram-generator --config config.yaml

  # Generate from command-line arguments
  aws-diagram-generator --name "Production" --region us-east-1 --tags "Environment=prod" "App=myapp"

  # Specify output directory and parallel workers
  aws-diagram-generator --config config.yaml --output ./docs --max-workers 5

  # Enable verbose logging
  aws-diagram-generator --config config.yaml --verbose
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'aws-diagram-generator {__version__}'
    )

    # Configuration source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '-c', '--config',
        type=str,
        help='Path to YAML configuration file (default: config.yaml)'
    )
    source_group.add_argument(
        '-n', '--name',
        type=str,
        help='Target name (use with --region and --tags)'
    )

    # CLI target arguments (only used with --name)
    parser.add_argument(
        '-r', '--region',
        type=str,
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '-t', '--tags',
        nargs='+',
        type=str,
        help='Resource tags in format "Key=Value" (can specify multiple)'
    )

    # Output options
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output',
        help='Output directory path (default: output)'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=MAX_WORKERS,
        help=f'Maximum parallel workers for processing multiple targets (default: {MAX_WORKERS})'
    )

    # LLM configuration
    parser.add_argument(
        '--model-id',
        type=str,
        default='us.anthropic.claude-sonnet-4-5-20250929-v1:0',
        help='AWS Bedrock model ID or inference profile (default: us.anthropic.claude-sonnet-4-5-20250929-v1:0)'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='LLM temperature (default: 0.1)'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=16384,
        help='Maximum tokens for LLM response (default: 16384)'
    )

    # Logging options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='aws_diagram_generator.log',
        help='Log file path (default: aws_diagram_generator.log)'
    )

    args = parser.parse_args()

    # Validate CLI target arguments
    if args.name:
        if not args.tags:
            parser.error("--name requires --tags to be specified")

    return args


def main() -> int:
    """Main CLI entry point."""
    try:
        # Load environment variables
        load_dotenv()

        # Parse arguments
        args = parse_arguments()

        # Setup logging
        setup_logging(args.verbose, args.log_file)
        logger = logging.getLogger(__name__)

        logger.info(f"AWS Architecture Diagram Generator v{__version__}")

        # Determine output directory
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)

        # Initialize LLM
        logger.info("Initializing LLM...")
        llm = initialize_llm(
            model_id=args.model_id,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )

        # Load targets
        targets = []

        if args.config:
            # Load from configuration file
            logger.info(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            if not config:
                logger.error("Failed to load valid configuration. Exiting.")
                return 1

            targets = config.get('targets', [])
            logger.info(f"Found {len(targets)} target(s) in configuration file")

        else:
            # Create target from CLI arguments
            logger.info(f"Creating target from CLI arguments: {args.name}")
            target = create_target_from_cli(args.name, args.region, args.tags)
            if not target:
                logger.error("Failed to create valid target from CLI arguments. Exiting.")
                return 1

            targets = [target]
            logger.info("Target created successfully from CLI arguments")

        if not targets:
            logger.error("No targets to process. Exiting.")
            return 1

        # Process targets
        if len(targets) == 1:
            # Single target - process directly
            logger.info("Processing single target")
            results = [process_target(targets[0], llm, output_dir)]
        else:
            # Multiple targets - process in parallel
            logger.info(f"Processing {len(targets)} targets in parallel")
            results = process_targets_parallel(targets, llm, args.max_workers, output_dir)

        # Print summary
        print_summary(results)

        # Return exit code based on results
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        if failed_count > 0:
            logger.warning(f"{failed_count} target(s) failed processing")
            return 1

        logger.info("All targets processed successfully")
        return 0

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.warning("Process interrupted by user")
        return 130

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in main execution: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
