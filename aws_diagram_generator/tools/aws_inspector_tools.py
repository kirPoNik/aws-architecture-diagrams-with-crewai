import boto3
import json
import logging
from crewai.tools import BaseTool
from typing import List, Dict, Any
from botocore.exceptions import ClientError
from time import sleep

logger = logging.getLogger(__name__)


class AWSEnvironmentScannerTool(BaseTool):
    name: str = "AWS Environment Scanner"
    description: str = "Scans a given AWS environment based on target configuration. The target can be tag-based or vpc-based."

    target_config: Dict[str, Any] = {}

    def _run(self, scan_request: str = "") -> str:
        """
        Uses boto3 to scan an AWS environment based on the target_config
        and return a JSON string of the infrastructure components.
        """
        if not self.target_config:
            return json.dumps({"error": "No target configuration provided to the scanner tool."})

        target = self.target_config
        target_name = target.get('name', 'Unknown Target')

        tags_to_filter = target.get('tags', [])
        aws_region = target.get('region', 'us-east-1')

        logger.info(f"Starting AWS scan for target: {target_name} in region: {aws_region}")

        try:
            infrastructure = self._scan_by_tags_globally(tags_to_filter, aws_region)

            def json_default_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

            return json.dumps(infrastructure, indent=2, default=json_default_serializer)

        except Exception as e:
            logger.error(f"Error during AWS scan: {e}", exc_info=True)
            return json.dumps({"error": f"Failed to scan AWS environment: {str(e)}"})

    def _scan_by_tags_globally(self, tags_to_filter: List, aws_region: str) -> List[Dict[str, Any]]:
        """
        Scans all resources matching tags using ResourceGroupsTaggingAPI and hydrates
        their configuration using AWS Config.
        """
        # Set default region for boto3
        boto3.setup_default_session(region_name=aws_region)
        tagging_client = boto3.client('resourcegroupstaggingapi')
        config_client = boto3.client('config')

        boto3_tag_filters = [{'Key': t['Key'], 'Values': [t['Value']]} for t in tags_to_filter]

        all_resource_mappings = []
        try:
            logger.info(f"Fetching resources with tags: {tags_to_filter}")
            paginator = tagging_client.get_paginator('get_resources')
            for page in paginator.paginate(TagFilters=boto3_tag_filters, ResourcesPerPage=100):
                resources = page.get('ResourceTagMappingList', [])
                all_resource_mappings.extend(resources)

            logger.info(f"Found {len(all_resource_mappings)} resources matching tags")

        except ClientError as e:
            logger.error(f"AWS API error getting resources from Tagging API: {e}")
            return [{"error": f"Failed to get resources from Tagging API: {str(e)}"}]
        except Exception as e:
            logger.error(f"Unexpected error getting resources: {e}")
            return [{"error": f"Failed to get resources from Tagging API: {str(e)}"}]

        if not all_resource_mappings:
            logger.warning("No resources found matching the specified tags")
            return []

        # Hydrate resource configurations using AWS Config with batch processing
        self._batch_hydrate_configurations(all_resource_mappings, config_client)

        return all_resource_mappings

    def _batch_hydrate_configurations(
        self,
        resources: List[Dict[str, Any]],
        config_client,
        batch_size: int = 20
    ) -> None:
        """
        Hydrate resource configurations using AWS Config batch API.
        Processes resources in batches to avoid rate limits.
        """
        logger.info(f"Hydrating configurations for {len(resources)} resources")

        # Group resources by type for more efficient querying
        resources_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for resource in resources:
            arn = resource['ResourceARN']
            resource_type = self._extract_resource_type_from_arn(arn)
            if resource_type:
                if resource_type not in resources_by_type:
                    resources_by_type[resource_type] = []
                resources_by_type[resource_type].append(resource)

        # Process each resource type
        for resource_type, type_resources in resources_by_type.items():
            logger.info(f"Processing {len(type_resources)} resources of type: {resource_type}")

            # Process in batches
            for i in range(0, len(type_resources), batch_size):
                batch = type_resources[i:i + batch_size]
                self._process_resource_batch(batch, config_client, resource_type)

                # Add small delay to avoid throttling
                if i + batch_size < len(type_resources):
                    sleep(0.1)

    def _extract_resource_type_from_arn(self, arn: str) -> str:
        """
        Extract AWS resource type from ARN.
        ARN format: arn:aws:service:region:account:resource-type/resource-id
        """
        try:
            parts = arn.split(':')
            if len(parts) >= 6:
                service = parts[2]
                resource_part = parts[5]

                # Handle different ARN formats
                if '/' in resource_part:
                    resource_type = resource_part.split('/')[0]
                else:
                    resource_type = resource_part

                # Map service to AWS Config resource type
                return self._map_service_to_config_type(service, resource_type)

        except Exception as e:
            logger.warning(f"Could not extract resource type from ARN {arn}: {e}")

        return None

    def _map_service_to_config_type(self, service: str, resource_type: str) -> str:
        """
        Map AWS service and resource type to AWS Config resource type.
        """
        # Common mappings - extend as needed
        mapping = {
            ('ec2', 'instance'): 'AWS::EC2::Instance',
            ('ec2', 'security-group'): 'AWS::EC2::SecurityGroup',
            ('ec2', 'vpc'): 'AWS::EC2::VPC',
            ('ec2', 'subnet'): 'AWS::EC2::Subnet',
            ('ec2', 'network-interface'): 'AWS::EC2::NetworkInterface',
            ('ec2', 'volume'): 'AWS::EC2::Volume',
            ('elasticloadbalancing', 'loadbalancer'): 'AWS::ElasticLoadBalancingV2::LoadBalancer',
            ('rds', 'db'): 'AWS::RDS::DBInstance',
            ('s3', ''): 'AWS::S3::Bucket',
            ('lambda', 'function'): 'AWS::Lambda::Function',
            ('dynamodb', 'table'): 'AWS::DynamoDB::Table',
        }

        return mapping.get((service, resource_type), f"AWS::{service.upper()}::{resource_type.capitalize()}")

    def _process_resource_batch(
        self,
        batch: List[Dict[str, Any]],
        config_client,
        resource_type: str
    ) -> None:
        """
        Process a batch of resources to fetch their configurations.
        Uses batch_get_resource_config when possible, falls back to individual queries.
        """
        # Try batch get first
        resource_keys = []
        for resource in batch:
            arn = resource['ResourceARN']
            resource_id = self._extract_resource_id_from_arn(arn)

            if resource_id:
                resource_keys.append({
                    'resourceType': resource_type,
                    'resourceId': resource_id
                })

        if resource_keys:
            try:
                response = config_client.batch_get_resource_config(
                    resourceKeys=resource_keys
                )

                # Match configurations back to resources
                configs_by_id = {
                    item['resourceId']: item
                    for item in response.get('baseConfigurationItems', [])
                }

                for resource in batch:
                    arn = resource['ResourceARN']
                    resource_id = self._extract_resource_id_from_arn(arn)

                    if resource_id in configs_by_id:
                        logger.debug(f"Found config for {arn}")
                        resource['Configuration'] = configs_by_id[resource_id]
                    else:
                        # Fall back to query-based approach
                        self._fetch_config_by_query(resource, config_client)

            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')

                if error_code == 'ValidationException':
                    # Batch get not supported for this resource type, use query fallback
                    logger.info(f"Batch get not supported for {resource_type}, using query method")
                    for resource in batch:
                        self._fetch_config_by_query(resource, config_client)
                else:
                    logger.error(f"Error in batch_get_resource_config: {e}")
                    for resource in batch:
                        resource['Configuration'] = None

            except Exception as e:
                logger.error(f"Unexpected error in batch processing: {e}")
                for resource in batch:
                    resource['Configuration'] = None

    def _extract_resource_id_from_arn(self, arn: str) -> str:
        """Extract resource ID from ARN."""
        try:
            parts = arn.split(':')
            if len(parts) >= 6:
                resource_part = parts[5]

                # Handle different formats
                if '/' in resource_part:
                    return resource_part.split('/', 1)[1]
                else:
                    return resource_part

        except Exception as e:
            logger.warning(f"Could not extract resource ID from ARN {arn}: {e}")

        return None

    def _fetch_config_by_query(self, resource: Dict[str, Any], config_client) -> None:
        """
        Fetch configuration for a single resource using Config query.
        Uses ARN-based query which is more reliable.
        """
        resource_arn = resource['ResourceARN']

        try:
            # Use configuration.arn which is more reliable than resourceId
            # Remove single quotes from ARN to prevent SQL injection issues
            safe_arn = resource_arn.replace("'", "''")

            # Query using ARN in configuration
            config_response = config_client.select_resource_config(
                Expression=f"SELECT * WHERE configuration.arn = '{safe_arn}'"
            )

            results = config_response.get('Results', [])
            if results:
                logger.debug(f"Found config for {resource_arn}")
                # Results are JSON strings, parse them
                config_data = json.loads(results[0]) if isinstance(results[0], str) else results[0]
                resource['Configuration'] = config_data
            else:
                logger.debug(f"No config found for {resource_arn}")
                resource['Configuration'] = None

        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'ThrottlingException':
                logger.warning(f"Throttled while fetching config for {resource_arn}, retrying...")
                sleep(1)
                # Retry once
                try:
                    config_response = config_client.select_resource_config(
                        Expression=f"SELECT * WHERE configuration.arn = '{safe_arn}'"
                    )
                    results = config_response.get('Results', [])
                    if results:
                        config_data = json.loads(results[0]) if isinstance(results[0], str) else results[0]
                        resource['Configuration'] = config_data
                    else:
                        resource['Configuration'] = None
                except Exception:
                    logger.error(f"Failed to fetch config for {resource_arn} after retry")
                    resource['Configuration'] = None
            else:
                logger.error(f"Error fetching config for {resource_arn}: {e}")
                resource['Configuration'] = None

        except Exception as e:
            logger.error(f"Unexpected error fetching config for {resource_arn}: {e}")
            resource['Configuration'] = None
