#!/usr/bin/env python3
"""Simple script to view all memory strategies for the current actor.

Usage:
    python view_memory.py              # Uses ACTOR_ID from .env
    python view_memory.py dini-123     # Specific actor ID
"""

import os
import sys

import boto3
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ["REGION_NAME"]
ENV = os.environ.get("ENV")


def get_memory_id():
    """Get memory ID from SSM Parameter Store."""
    ssm = boto3.client("ssm", region_name=REGION_NAME)
    param_name = f"/agent-core-stack-{ENV}/memory-id"

    try:
        response = ssm.get_parameter(Name=param_name)
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        print(f"❌ Memory ID not found in SSM: {param_name}")
        print("   Deploy the stack first: make deploy")
        sys.exit(1)


def view_strategy(client, memory_id, strategy_name, namespace):
    """View records from a specific memory strategy."""
    print(f"\n{'=' * 80}")
    print(f"📝 {strategy_name.upper()} MEMORY")
    print(f"{'=' * 80}")
    print(f"Namespace: {namespace}")
    print()

    try:
        # List all records (no search query = get all)
        response = client.list_memory_records(
            memoryId=memory_id, namespace=namespace, maxResults=20
        )

        records = response.get("memoryRecordSummaries", [])

        if not records:
            print("  (No records found)")
            return

        for i, record in enumerate(records, 1):
            # Extract text from content
            content_obj = record.get("content", {})
            if isinstance(content_obj, dict):
                text = content_obj.get("text", "[No text]")
            else:
                text = str(content_obj)

            created = record.get("createdAt", "Unknown")
            print(f"  {i}. {text}")
            print(f"     Created: {created}")
            print()

    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    """View all memory strategies."""
    # Get actor ID from command line or environment
    if len(sys.argv) > 1:
        actor_id = sys.argv[1]
    else:
        actor_id = os.environ.get("ACTOR_ID")
        if not actor_id:
            print("❌ Error: ACTOR_ID not set")
            print("\nUsage:")
            print("  Set ACTOR_ID in .env file, or")
            print(f"  python {sys.argv[0]} <actor-id>")
            sys.exit(1)

    # Get memory ID and client
    memory_id = get_memory_id()
    client = boto3.client("bedrock-agentcore", region_name=REGION_NAME)

    print(f"\n{'=' * 80}")
    print("AGENTCORE MEMORY VIEWER")
    print(f"{'=' * 80}")
    print(f"Memory ID: {memory_id}")
    print(f"Actor ID:  {actor_id}")
    print(f"{'=' * 80}")

    # View each strategy
    view_strategy(client, memory_id, "Preference", f"/preferences/{actor_id}/")

    view_strategy(client, memory_id, "Semantic", f"/facts/{actor_id}/")

    view_strategy(client, memory_id, "Summary", f"/summaries/{actor_id}/")

    print(f"\n{'=' * 80}")
    print("💡 TIP: Summary memory is session-scoped - provide session_id to view:")
    print(f"         /summaries/{actor_id}/<session-id>/")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
