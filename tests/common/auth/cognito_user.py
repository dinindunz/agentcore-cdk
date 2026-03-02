"""Cognito user validation for AgentCore invocations.

This module provides user validation against Cognito User Pool to ensure
only authorized actors can invoke the agent.
"""

import json
import os
import sys

import boto3


def validate_and_lookup_actor(
    preferred_username: str,
    region_name: str | None = None,
    user_pool_id: str | None = None,
) -> str:
    """
    Validate actor exists in Cognito and return their Cognito username.

    Looks up the user by preferred_username, validates they exist,
    and returns their Cognito username (UUID) for use as actor_id.

    Args:
        preferred_username: User's preferred_username from .env (e.g., "actor-123")
        region_name: AWS region (defaults to REGION_NAME env var)
        user_pool_id: Cognito User Pool ID (auto-fetched from Secrets Manager if not provided)

    Returns:
        Cognito username (UUID) that's valid for AgentCore Memory

    Exits:
        Exits with code 1 if user not found or validation fails
    """
    region = region_name or os.environ.get("REGION_NAME")

    # Get User Pool ID if not provided
    if not user_pool_id:
        sm = boto3.client("secretsmanager", region_name=region)
        try:
            agent_cognito = json.loads(
                sm.get_secret_value(SecretId="agent-core-stack-dev/agent-cognito")["SecretString"]
            )
            user_pool_id = agent_cognito["user_pool_id"]
        except Exception as e:
            print(f"\n❌ Error: Could not fetch User Pool ID: {e}")
            print("   Aborting invocation.\n")
            sys.exit(1)

    # Validate user exists in pool
    cognito = boto3.client("cognito-idp", region_name=region)

    try:
        # Look up user by preferred_username
        response = cognito.list_users(
            UserPoolId=user_pool_id,
            Filter=f'preferred_username = "{preferred_username}"',
            Limit=1,
        )

        if response.get("Users"):
            username = response["Users"][0]["Username"]
            print(f"✓ Validated user '{preferred_username}' → Cognito username '{username}'")
            return username
        else:
            print(f"\n❌ Error: User '{preferred_username}' not found in Cognito User Pool")
            print(f"   Create user with: python scripts/create_user.py {preferred_username}")
            print("   Or run: make create-user")
            print("   Aborting invocation.\n")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: Could not validate actor: {e}")
        print("   Aborting invocation.\n")
        sys.exit(1)
