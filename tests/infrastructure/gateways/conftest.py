"""Shared fixtures for gateway infrastructure tests."""

import os

import boto3
import pytest


@pytest.fixture(scope="session")
def region_name():
    """AWS region from environment."""
    region = os.getenv("REGION_NAME", "ap-southeast-2")
    return region


@pytest.fixture(scope="session")
def iam_gateway_url(region_name):
    """Fetch IAM gateway URL from SSM."""
    ssm = boto3.client("ssm", region_name=region_name)
    try:
        response = ssm.get_parameter(Name="/agent-core-stack-dev/iam-gateway-url")
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        pytest.skip("IAM gateway URL not found in SSM - stack not deployed")


@pytest.fixture(scope="session")
def jwt_gateway_url(region_name):
    """Fetch JWT gateway URL from SSM."""
    ssm = boto3.client("ssm", region_name=region_name)
    try:
        response = ssm.get_parameter(Name="/agent-core-stack-dev/jwt-gateway-url")
        return response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        pytest.skip("JWT gateway URL not found in SSM - stack not deployed")


@pytest.fixture(scope="session")
def test_actor_id():
    """Use consistent test actor ID across all infrastructure tests."""
    return "test-user"
