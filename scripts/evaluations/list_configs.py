#!/usr/bin/env python3
"""List online evaluation configurations."""

import json
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

region = os.getenv("REGION_NAME", "ap-southeast-2")

# Initialise Bedrock AgentCore Control client (for control plane operations)
client = boto3.client("bedrock-agentcore-control", region_name=region)


def list_online_eval_configs():
    """List all online evaluation configurations."""
    try:
        response = client.list_online_evaluation_configs()
        configs = response.get("onlineEvaluationConfigs", [])

        if not configs:
            print("No online evaluation configurations found.")
            return

        print(f"\nFound {len(configs)} evaluation configuration(s):\n")

        for config in configs:
            config_id = config.get("onlineEvaluationConfigId")

            print("=" * 80)
            print(f"Config Name: {config.get('onlineEvaluationConfigName')}")
            print(f"Config ID: {config_id}")
            print(f"Status: {config.get('status')}")
            print(f"Execution Status: {config.get('executionStatus')}")
            print(f"Description: {config.get('description', 'N/A')}")
            print(f"Created: {config.get('createdAt', 'N/A')}")
            print(f"Updated: {config.get('updatedAt', 'N/A')}")

            # Fetch full details to get evaluators
            try:
                details = client.get_online_evaluation_config(onlineEvaluationConfigId=config_id)

                agent_id = details.get("agentId", "N/A")
                sampling_rate = details.get("samplingRate", "N/A")
                evaluators = details.get("evaluators", [])

                print(f"\nAgent ID: {agent_id}")
                print(f"Sampling Rate: {sampling_rate}%")
                print(f"\nEvaluators ({len(evaluators)}):")

                for evaluator in evaluators:
                    # Evaluators can be built-in (dict with evaluatorId) or custom (dict with evaluatorArn)
                    if isinstance(evaluator, str):
                        print(f"  - {evaluator}")
                    elif isinstance(evaluator, dict):
                        # Check if it's a built-in evaluator (has evaluatorId starting with Builtin.)
                        evaluator_id = evaluator.get("evaluatorId", "")
                        evaluator_arn = evaluator.get("evaluatorArn", "")

                        if evaluator_id.startswith("Builtin."):
                            print(f"  - Built-in: {evaluator_id}")
                        elif evaluator_arn:
                            # Custom evaluator with ARN
                            if "/" in evaluator_arn:
                                evaluator_name = evaluator_arn.split("/")[-1]
                                print(f"  - Custom: {evaluator_name}")
                                print(f"    ARN: {evaluator_arn}")
                            else:
                                print(f"  - Custom: {evaluator_arn}")
                        elif evaluator_id:
                            # Has evaluatorId but not Builtin
                            print(f"  - {evaluator_id}")
                        else:
                            print(f"  - {evaluator}")
                    else:
                        print(f"  - {evaluator}")

            except Exception as detail_error:
                print(f"\n⚠️  Could not fetch detailed config: {detail_error}")
                print("  (Evaluator list not available)")

            print()

    except Exception as e:
        print(f"Error listing evaluation configs: {e}", file=sys.stderr)
        sys.exit(1)


def get_eval_config_details(config_id: str):
    """Get detailed information about a specific evaluation configuration."""
    try:
        response = client.get_online_evaluation_config(onlineEvaluationConfigId=config_id)

        print("\nDetailed Configuration:")
        print("=" * 80)
        print(json.dumps(response, indent=2, default=str))

    except Exception as e:
        print(f"Error getting evaluation config details: {e}", file=sys.stderr)


if __name__ == "__main__":
    # List all configurations
    list_online_eval_configs()

    # If config ID is provided, show detailed info
    if len(sys.argv) > 1:
        config_id = sys.argv[1]
        print(f"\nFetching details for config ID: {config_id}")
        get_eval_config_details(config_id)
