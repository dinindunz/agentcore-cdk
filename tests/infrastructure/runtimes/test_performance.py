"""Basic performance benchmarks for runtime invocations."""

import json
import time
from urllib.parse import quote

import boto3
import pytest


@pytest.mark.infrastructure
@pytest.mark.slow
def test_agent_response_time(agent_runtime_arn, region_name, test_actor_id):
    """Measure agent response time for simple query (not a strict performance test)."""
    secrets_manager = boto3.client("secretsmanager", region_name=region_name)
    secret = secrets_manager.get_secret_value(SecretId="agent-core-stack-dev/agent-cognito")
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

    url = f"https://bedrock-agentcore.{region_name}.amazonaws.com/runtimes/{quote(agent_runtime_arn, safe='')}/invocations?qualifier=DEFAULT"

    payload = {
        "sessionId": "test-session-perf",
        "actorId": test_actor_id,
        "input": {"value": "What is 2 + 2?"},
    }

    start_time = time.time()
    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    duration = time.time() - start_time

    assert response.status_code == 200

    # Not a strict assertion - just informational
    # Agent should respond within reasonable time (< 30 seconds)
    print(f"\n⏱️  Agent response time: {duration:.2f}s")
    assert duration < 30, f"Agent took too long: {duration:.2f}s"


@pytest.mark.infrastructure
def test_mcp_runtime_response_time(mcp_calculator_runtime_arn, region_name):
    """Measure MCP runtime response time (should be faster than agent)."""
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
        "method": "tools/call",
        "params": {
            "name": "add",
            "arguments": {"a": 2, "b": 2},
        },
    }

    start_time = time.time()
    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    duration = time.time() - start_time

    assert response.status_code == 200

    # MCP runtime should be fast (< 5 seconds)
    print(f"\n⏱️  MCP runtime response time: {duration:.2f}s")
    assert duration < 5, f"MCP runtime took too long: {duration:.2f}s"
