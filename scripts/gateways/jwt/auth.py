"""JWT authentication module for AgentCore Gateway.

This module provides reusable authentication logic for invoking JWT-authenticated
AgentCore gateways using Cognito OAuth2 client_credentials flow.
"""

import json
import os
from typing import Any

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ["REGION_NAME"]


def get_gateway_url() -> str:
    """Fetch the JWT gateway URL from SSM Parameter Store.

    Returns:
        str: The JWT gateway URL
    """
    ssm_client = boto3.client("ssm", region_name=REGION_NAME)
    return ssm_client.get_parameter(Name="/agent-core-stack-dev/jwt-gateway-url")[
        "Parameter"
    ]["Value"]


def get_access_token() -> str:
    """Get OAuth2 access token from Cognito using client_credentials flow.

    Returns:
        str: The access token for Bearer authentication
    """
    sm_client = boto3.client("secretsmanager", region_name=REGION_NAME)

    # Fetch Cognito credentials from Secrets Manager
    gateway_cognito = json.loads(
        sm_client.get_secret_value(SecretId="agent-core-stack-dev/gateway-cognito")[
            "SecretString"
        ]
    )

    # Get OAuth2 access token using client_credentials flow
    token_response = requests.post(
        gateway_cognito["token_endpoint"],
        data={
            "grant_type": "client_credentials",
            "scope": "gateway/invoke",
        },
        auth=(gateway_cognito["client_id"], gateway_cognito["client_secret"]),
    )
    token_response.raise_for_status()
    return token_response.json()["access_token"]


def get_headers(include_event_stream: bool = True) -> dict[str, str]:
    """Get authenticated headers for JWT gateway requests.

    Args:
        include_event_stream: Whether to include text/event-stream in Accept header

    Returns:
        dict: Headers with Bearer token authentication
    """
    access_token = get_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    if include_event_stream:
        headers["Accept"] = "application/json, text/event-stream"

    return headers


def make_request(
    payload: dict[str, Any],
    include_event_stream: bool = True,
) -> requests.Response:
    """Make an authenticated request to the JWT gateway.

    Args:
        payload: The JSON-RPC payload to send
        include_event_stream: Whether to include text/event-stream in Accept header

    Returns:
        requests.Response: The response from the gateway
    """
    gateway_url = get_gateway_url()
    headers = get_headers(include_event_stream=include_event_stream)

    return requests.post(gateway_url, headers=headers, json=payload)
