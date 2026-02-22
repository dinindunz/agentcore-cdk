#!/usr/bin/env python3
"""Create a Phoenix project by sending a minimal trace to establish the project namespace."""

import argparse
import json
import sys

import boto3


def get_stack_outputs(stack_name: str, region: str) -> dict:
    """Fetch CloudFormation stack outputs."""
    cfn = boto3.client("cloudformation", region_name=region)
    response = cfn.describe_stacks(StackName=stack_name)
    outputs = response["Stacks"][0]["Outputs"]
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def get_phoenix_api_key(secret_arn: str, region: str) -> str:
    """Fetch Phoenix API key from Secrets Manager."""
    sm = boto3.client("secretsmanager", region_name=region)
    response = sm.get_secret_value(SecretId=secret_arn)
    secret = json.loads(response["SecretString"])
    return secret["api_key"]


def create_project(phoenix_url: str, api_key: str, project_name: str) -> None:
    """Create a Phoenix project using the GraphQL API."""
    import requests

    # GraphQL mutation to create a project
    mutation = """
    mutation CreateProject($input: CreateProjectInput!) {
        createProject(input: $input) {
            project {
                id
                name
            }
        }
    }
    """

    variables = {
        "input": {
            "name": project_name,
            "description": f"AgentCore observability project for {project_name}",
        }
    }

    # Send GraphQL request
    response = requests.post(
        f"{phoenix_url}/graphql",
        json={"query": mutation, "variables": variables},
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    if response.status_code != 200:
        raise Exception(
            f"Failed to create project: HTTP {response.status_code} - {response.text}"
        )

    result = response.json()
    if "errors" in result:
        # Check if the error is about project already existing
        errors = result["errors"]
        if any(
            "already exists" in str(error.get("message", "")).lower()
            for error in errors
        ):
            print(
                f"✓ Phoenix project '{project_name}' already exists - skipping creation"
            )
            return
        raise Exception(f"GraphQL errors: {result['errors']}")

    project_id = result["data"]["createProject"]["project"]["id"]
    print(f"✓ Phoenix project '{project_name}' created successfully (ID: {project_id})")


def main():
    parser = argparse.ArgumentParser(
        description="Create a Phoenix project for observability"
    )
    parser.add_argument(
        "--stack-name",
        help="CloudFormation stack name",
    )
    parser.add_argument(
        "--project-name",
        help="Phoenix project name",
    )
    parser.add_argument(
        "--region",
        help="AWS region",
    )
    args = parser.parse_args()

    print(f"Creating Phoenix project '{args.project_name}'...")

    # Get Phoenix endpoint and API key from stack outputs
    outputs = get_stack_outputs(args.stack_name, args.region)
    phoenix_url = outputs["PhoenixUrl"]
    api_key_secret_arn = outputs["PhoenixApiKeySecretArn"]

    print(f"Phoenix endpoint: {phoenix_url}")

    # Fetch API key
    api_key = get_phoenix_api_key(api_key_secret_arn, args.region)

    # Create project
    create_project(phoenix_url, api_key, args.project_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
