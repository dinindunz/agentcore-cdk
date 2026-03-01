"""Infrastructure tests for agent runtime end-to-end invocation."""

import json
from urllib.parse import quote

import boto3
import pytest


@pytest.mark.infrastructure
def test_agent_simple_calculation(agent_runtime_arn, region_name, test_actor_id):
    """Test agent can perform simple calculation using tools."""
    # Get auth credentials
    secrets_manager = boto3.client("secretsmanager", region_name=region_name)
    secret = secrets_manager.get_secret_value(SecretId="agent-core-stack-dev/agent-cognito")
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

    # Invoke agent with simple calculation
    url = f"https://bedrock-agentcore.{region_name}.amazonaws.com/runtimes/{quote(agent_runtime_arn, safe='')}/invocations?qualifier=DEFAULT"

    payload = {
        "sessionId": "test-session-calculation",
        "actorId": test_actor_id,
        "input": {"value": "What is 15 + 27?"},
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

    assert "output" in data
    assert "value" in data["output"]
    # Agent should calculate 15 + 27 = 42
    assert "42" in data["output"]["value"]


@pytest.mark.infrastructure
def test_agent_returns_structured_response(agent_runtime_arn, region_name, test_actor_id):
    """Test agent returns properly structured response."""
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
        "sessionId": "test-session-structure",
        "actorId": test_actor_id,
        "input": {"value": "Hello"},
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

    # Verify response structure
    assert "sessionId" in data
    assert "actorId" in data
    assert "output" in data
    assert "value" in data["output"]
    assert data["sessionId"] == "test-session-structure"
    assert data["actorId"] == test_actor_id
