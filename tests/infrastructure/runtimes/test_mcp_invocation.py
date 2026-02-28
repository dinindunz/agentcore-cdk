"""Infrastructure tests for MCP runtime direct invocation."""

import json
from urllib.parse import quote

import boto3
import pytest


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
        },
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert "result" in data
    assert data["result"]["content"][0]["text"] == "15"


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
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "result" in data
    assert "tools" in data["result"]
    tools = data["result"]["tools"]
    assert len(tools) > 0

    # Verify add tool exists
    tool_names = [t["name"] for t in tools]
    assert "add" in tool_names
