"""Infrastructure tests for MCP runtime direct invocation."""

import json
from urllib.parse import quote

import boto3
import pytest


def parse_sse_response(response_text: str) -> dict:
    """Parse Server-Sent Events (SSE) response to extract JSON data.

    Args:
        response_text: Raw SSE response text

    Returns:
        Parsed JSON data from the SSE event
    """
    # SSE format: "event: message\r\ndata: {...}\r\n\r\n"
    for line in response_text.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            json_str = line[6:]  # Remove "data: " prefix
            return json.loads(json_str)
    raise ValueError(f"No data found in SSE response: {response_text}")


@pytest.mark.infrastructure
def test_mcp_calculator_add(mcp_calculator_runtime_arn, region_name):
    """Test MCP calculator runtime can perform addition."""
    # Get auth credentials
    secrets_manager = boto3.client("secretsmanager", region_name=region_name)
    secret = secrets_manager.get_secret_value(SecretId="agent-core-stack-dev/mcp-cognito")
    credentials = json.loads(secret["SecretString"])

    # Get access token
    import requests

    token_response = requests.post(
        credentials["token_endpoint"],
        data={
            "grant_type": "client_credentials",
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]

    # Invoke MCP runtime
    url = f"https://bedrock-agentcore.{region_name}.amazonaws.com/runtimes/{quote(mcp_calculator_runtime_arn, safe='')}/invocations?qualifier=DEFAULT"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "add",
            "arguments": {"a": 10, "b": 5},
        },
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    # Parse SSE response to extract JSON
    data = parse_sse_response(response.text)

    assert "result" in data
    assert data["result"]["content"][0]["text"] == "15.0"


@pytest.mark.infrastructure
def test_mcp_calculator_list_tools(mcp_calculator_runtime_arn, region_name):
    """Test MCP calculator runtime lists available tools."""
    secrets_manager = boto3.client("secretsmanager", region_name=region_name)
    secret = secrets_manager.get_secret_value(SecretId="agent-core-stack-dev/mcp-cognito")
    credentials = json.loads(secret["SecretString"])

    import requests

    token_response = requests.post(
        credentials["token_endpoint"],
        data={
            "grant_type": "client_credentials",
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    access_token = token_response.json()["access_token"]

    url = f"https://bedrock-agentcore.{region_name}.amazonaws.com/runtimes/{quote(mcp_calculator_runtime_arn, safe='')}/invocations?qualifier=DEFAULT"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )

    assert response.status_code == 200

    # Parse SSE response to extract JSON
    data = parse_sse_response(response.text)

    assert "result" in data
    assert "tools" in data["result"]
    tools = data["result"]["tools"]
    assert len(tools) > 0

    # Verify add tool exists
    tool_names = [t["name"] for t in tools]
    assert "add" in tool_names
