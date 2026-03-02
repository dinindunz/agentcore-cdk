#!/usr/bin/env python3
"""List all users in the Cognito User Pool."""

import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ.get("REGION_NAME")


def list_users(user_pool_id: str) -> None:
    """List all users in the pool."""
    cognito = boto3.client("cognito-idp", region_name=REGION_NAME)

    try:
        response = cognito.list_users(UserPoolId=user_pool_id, Limit=60)

        users = response.get("Users", [])

        if not users:
            print("No users found in the pool")
            return

        print(f"Found {len(users)} user(s):\n")

        for user in users:
            username = user.get("Username")
            status = user.get("UserStatus")
            enabled = user.get("Enabled", True)

            # Extract attributes
            attributes = {attr["Name"]: attr["Value"] for attr in user.get("Attributes", [])}
            email = attributes.get("email", "N/A")
            preferred_username = attributes.get("preferred_username", "N/A")

            print(f"Username: {username}")
            print(f"  Preferred Username: {preferred_username}")
            print(f"  Email: {email}")
            print(f"  Status: {status}")
            print(f"  Enabled: {enabled}")
            print()

    except Exception as e:
        print(f"Error listing users: {e}")


def main():
    """CLI entry point."""
    # Get User Pool ID from Secrets Manager
    sm = boto3.client("secretsmanager", region_name=REGION_NAME)
    secret = json.loads(
        sm.get_secret_value(SecretId="agent-core-stack-dev/agent-cognito")["SecretString"]
    )
    user_pool_id = secret["user_pool_id"]

    print(f"User Pool ID: {user_pool_id}\n")
    list_users(user_pool_id)


if __name__ == "__main__":
    main()
