"""Shared fixtures for runtime infrastructure tests."""

import os

import boto3
import pytest


@pytest.fixture(scope="session")
def region_name():
    """AWS region from environment."""
    region = os.getenv("REGION_NAME", "ap-southeast-2")
    return region


@pytest.fixture(scope="session")
def agent_runtime_arn(region_name):
    """Fetch agent runtime ARN from SSM."""
    ssm = boto3.client("ssm", region_name=region_name)
    try:
        response = ssm.get_parameter(Name="/agent-core-stack-dev/agent-runtime-arn")
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        pytest.skip("Agent runtime ARN not found in SSM - stack not deployed")


@pytest.fixture(scope="session")
def mcp_calculator_runtime_arn(region_name):
    """Fetch MCP calculator runtime ARN from SSM."""
    ssm = boto3.client("ssm", region_name=region_name)
    try:
        response = ssm.get_parameter(Name="/agent-core-stack-dev/mcp-calculator-runtime-arn")
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        pytest.skip("MCP calculator runtime ARN not found in SSM - stack not deployed")


@pytest.fixture(scope="session")
def test_actor_id():
    """Use consistent test actor ID across all infrastructure tests."""
    return "test-user"
