"""IAM authentication module for AgentCore Gateway.

This module provides reusable authentication logic for invoking IAM-authenticated
AgentCore gateways using AWS SigV4 signing.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Any

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ["REGION_NAME"]
SERVICE_NAME = "bedrock-agentcore"


def get_gateway_url() -> str:
    """Fetch the IAM gateway URL from SSM Parameter Store.

    Returns:
        str: The IAM gateway URL
    """
    ssm_client = boto3.client("ssm", region_name=REGION_NAME)
    return ssm_client.get_parameter(Name="/agent-core-stack-dev/iam-gateway-url")["Parameter"][
        "Value"
    ]


def get_credentials():
    """Get AWS credentials for SigV4 signing.

    Returns:
        FrozenCredentials: AWS credentials from the current session
    """
    session = boto3.Session(region_name=REGION_NAME)
    return session.get_credentials().get_frozen_credentials()


def get_signed_headers(
    url: str,
    payload: str,
    include_event_stream: bool = True,
) -> dict[str, str]:
    """Get SigV4 signed headers for IAM gateway requests.

    Args:
        url: The gateway URL
        payload: The JSON payload as a string
        include_event_stream: Whether to include text/event-stream in Accept header

    Returns:
        dict: Headers with SigV4 signature
    """
    credentials = get_credentials()

    headers = {
        "Content-Type": "application/json",
    }

    if include_event_stream:
        headers["Accept"] = "application/json, text/event-stream"

    # Create AWS request and sign it
    request = AWSRequest(method="POST", url=url, data=payload, headers=headers)
    SigV4Auth(credentials, SERVICE_NAME, REGION_NAME).add_auth(request)

    return dict(request.headers)


def make_request(
    payload: dict[str, Any],
    include_event_stream: bool = True,
) -> tuple[int, dict[str, Any] | str]:
    """Make an authenticated SigV4-signed request to the IAM gateway.

    Args:
        payload: The JSON-RPC payload to send
        include_event_stream: Whether to include text/event-stream in Accept header

    Returns:
        tuple: (status_code, response_data)

    Raises:
        urllib.error.HTTPError: If the request fails
    """
    gateway_url = get_gateway_url()
    payload_str = json.dumps(payload)
    headers = get_signed_headers(
        gateway_url,
        payload_str,
        include_event_stream=include_event_stream,
    )

    req = urllib.request.Request(
        gateway_url,
        data=payload_str.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
