"""Pytest fixtures for AgentCore memory integration tests.

These fixtures provide common setup for integration tests that interact
with the live AWS AgentCore service.
"""

import os
import pytest
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def aws_region():
    """AWS region for testing."""
    return os.environ.get("REGION_NAME")


@pytest.fixture(scope="session")
def environment():
    """Deployment environment (dev, staging, prod)."""
    return os.environ.get("ENV", "dev")


@pytest.fixture(scope="session")
def test_actor_id():
    """Actor ID for integration tests.

    Uses 'test-user' as the standard test actor to avoid polluting
    production user data.
    """
    return "test-user"


@pytest.fixture(scope="session")
def memory_id(aws_region, environment):
    """Get AgentCore memory ID from SSM Parameter Store.

    Raises:
        pytest.skip: If memory ID not found (stack not deployed)
    """
    ssm = boto3.client("ssm", region_name=aws_region)
    param_name = f"/agent-core-stack-{environment}/memory-id"

    try:
        response = ssm.get_parameter(Name=param_name)
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        pytest.skip(f"Memory ID not found in SSM: {param_name}. Deploy stack first.")


@pytest.fixture(scope="session")
def bedrock_agentcore_client(aws_region):
    """Boto3 client for bedrock-agentcore service."""
    return boto3.client("bedrock-agentcore", region_name=aws_region)


@pytest.fixture
def unique_session_id():
    """Generate unique session ID for test isolation.

    Returns a new UUID-based session ID for each test to prevent
    test interference.
    """
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}"
