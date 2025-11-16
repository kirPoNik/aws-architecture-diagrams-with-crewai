import yaml
import json
import traceback

from tools.aws_inspector_tools import AWSEnvironmentScannerTool

def test_aws_scanner():
    """Test the AWS Environment Scanner Tool"""

    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Test each target
    for target in config.get('targets', []):
        print(f"Testing Target: {target.get('name', 'Unknown')}")
        print(f"Region: {target.get('region', 'Not specified')}")
        print(f"Tags: {target.get('tags', [])}")

        # Create the scanner tool with the target configuration
        aws_scanner_tool = AWSEnvironmentScannerTool(target_config=target)

        # Run the scan (the scan_request parameter is optional)
        try:
            result = aws_scanner_tool._run()

            # Parse and pretty-print the result
            print("Scan Results:")
            parsed_result = json.loads(result) if isinstance(result, str) else result
            # print(json.dumps(parsed_result, indent=2))

        except Exception as e:
            print(f"Error during scan: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    test_aws_scanner()