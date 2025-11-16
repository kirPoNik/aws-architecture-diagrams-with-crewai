"""Configuration management for AWS architecture diagram generator."""

import yaml
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate the configuration structure."""
    if not config:
        logger.error("Configuration is empty")
        return False

    targets = config.get('targets', [])
    if not targets:
        logger.error("No targets found in configuration")
        return False

    for idx, target in enumerate(targets):
        if not isinstance(target, dict):
            logger.error(f"Target {idx} is not a dictionary")
            return False

        if 'name' not in target:
            logger.error(f"Target {idx} missing required field 'name'")
            return False

        if 'tags' not in target:
            logger.error(f"Target '{target.get('name')}' missing required field 'tags'")
            return False

        if not isinstance(target['tags'], list):
            logger.error(f"Target '{target.get('name')}' tags must be a list")
            return False

        for tag in target['tags']:
            if not isinstance(tag, dict) or 'Key' not in tag or 'Value' not in tag:
                logger.error(f"Target '{target.get('name')}' has invalid tag format")
                return False

    logger.info(f"Configuration validated successfully with {len(targets)} target(s)")
    return True


def validate_target(target: Dict[str, Any]) -> bool:
    """Validate a single target configuration."""
    if not isinstance(target, dict):
        logger.error("Target is not a dictionary")
        return False

    if 'name' not in target:
        logger.error("Target missing required field 'name'")
        return False

    if 'tags' not in target:
        logger.error(f"Target '{target.get('name')}' missing required field 'tags'")
        return False

    if not isinstance(target['tags'], list):
        logger.error(f"Target '{target.get('name')}' tags must be a list")
        return False

    for tag in target['tags']:
        if not isinstance(tag, dict) or 'Key' not in tag or 'Value' not in tag:
            logger.error(f"Target '{target.get('name')}' has invalid tag format")
            return False

    return True


def load_config(config_path: str = 'config.yaml') -> Optional[Dict[str, Any]]:
    """Load and validate configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        if not validate_config(config):
            return None

        return config
    except FileNotFoundError:
        logger.error(f"Configuration file '{config_path}' not found")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        return None


def create_target_from_cli(name: str, region: str, tags: List[str]) -> Optional[Dict[str, Any]]:
    """
    Create a target configuration from CLI arguments.

    Args:
        name: Target name
        region: AWS region
        tags: List of tag strings in format "Key=Value"

    Returns:
        Target dictionary or None if invalid
    """
    try:
        # Parse tags from "Key=Value" format
        parsed_tags = []
        for tag_str in tags:
            if '=' not in tag_str:
                logger.error(f"Invalid tag format '{tag_str}'. Expected format: Key=Value")
                return None

            key, value = tag_str.split('=', 1)
            parsed_tags.append({'Key': key.strip(), 'Value': value.strip()})

        target = {
            'name': name,
            'region': region,
            'tags': parsed_tags
        }

        if not validate_target(target):
            return None

        return target

    except Exception as e:
        logger.error(f"Error creating target from CLI arguments: {e}")
        return None
