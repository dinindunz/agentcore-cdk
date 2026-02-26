#!/usr/bin/env python3
"""Query evaluation results from CloudWatch Logs."""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

region = os.getenv("REGION_NAME")

# Initialise CloudWatch Logs client
logs_client = boto3.client("logs", region_name=region)


def list_evaluation_log_groups():
    """List all log groups related to evaluations."""
    try:
        response = logs_client.describe_log_groups(
            logGroupNamePrefix="/aws/bedrock-agentcore/evaluations/"
        )

        log_groups = response.get("logGroups", [])

        if not log_groups:
            print("No evaluation log groups found.")
            print("\nThis could mean:")
            print("  1. The evaluation hasn't run yet (trigger it by using the agent)")
            print("  2. The evaluation is disabled")
            print("  3. Logs haven't been created yet")
            return []

        print(f"\nFound {len(log_groups)} evaluation log group(s):\n")

        for lg in log_groups:
            print("=" * 80)
            print(f"Log Group: {lg['logGroupName']}")
            print(f"Created: {datetime.fromtimestamp(lg['creationTime'] / 1000)}")
            print(f"Storage: {lg.get('storedBytes', 0)} bytes")
            print()

        return [lg["logGroupName"] for lg in log_groups]

    except Exception as e:
        print(f"Error listing log groups: {e}", file=sys.stderr)
        return []


def query_recent_evaluations(log_group_name: str, hours: int = 1):
    """Query recent evaluation results using CloudWatch Logs Insights."""
    try:
        # Query for the last N hours
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
        end_time = int(datetime.now().timestamp())

        # CloudWatch Logs Insights query
        query = """
        fields @timestamp, @message
        | filter @message like /evaluation/
        | sort @timestamp desc
        | limit 20
        """

        print(f"\nQuerying {log_group_name} for evaluations in the last {hours} hour(s)...")

        response = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            queryString=query,
        )

        query_id = response["queryId"]

        # Wait for query to complete
        import time

        while True:
            result = logs_client.get_query_results(queryId=query_id)
            status = result["status"]

            if status in ["Complete", "Failed", "Cancelled"]:
                break

            time.sleep(0.5)

        if status == "Complete":
            results = result.get("results", [])

            if not results:
                print(f"No evaluation results found in the last {hours} hour(s).")
                print("\nTry:")
                print("  1. Using the agent to trigger evaluations")
                print("  2. Increasing the time window (pass hours as second argument)")
                return

            print(f"\nFound {len(results)} evaluation result(s):\n")

            for i, fields in enumerate(results, 1):
                print(f"Result {i}:")
                print("-" * 80)

                for field in fields:
                    field_name = field["field"]
                    field_value = field["value"]

                    if field_name == "@message":
                        # Try to pretty-print JSON messages
                        try:
                            msg = json.loads(field_value)
                            print(json.dumps(msg, indent=2))
                        except (json.JSONDecodeError, ValueError):
                            print(field_value)
                    else:
                        print(f"{field_name}: {field_value}")

                print()
        else:
            print(f"Query failed with status: {status}")

    except Exception as e:
        print(f"Error querying evaluations: {e}", file=sys.stderr)


def main():
    hours = 1
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except ValueError:
            print("Usage: python query_results.py [hours]")
            print("  hours: number of hours to look back (default: 1)")
            sys.exit(1)

    # List all evaluation log groups
    log_groups = list_evaluation_log_groups()

    # Query each log group for recent evaluations
    for log_group in log_groups:
        query_recent_evaluations(log_group, hours)


if __name__ == "__main__":
    main()
