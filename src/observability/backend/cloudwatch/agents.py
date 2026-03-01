"""Agent discovery from CloudWatch log groups."""

import re
from datetime import datetime

import boto3

from ..config import Config
from ..models import Agent


def extract_runtime_name(log_group_name: str) -> str:
    """Extract runtime name from log group path.

    Args:
        log_group_name: CloudWatch log group name

    Returns:
        Extracted runtime name
    """
    # Pattern: /aws/bedrock-agentcore/runtimes/{stack_name}_{runtime_name}/...
    match = re.search(r"/runtimes/([^/]+)", log_group_name)
    if match:
        return match.group(1)
    return log_group_name


def discover_agents(region: str | None = None) -> list[Agent]:
    """Discover AgentCore runtimes from CloudWatch log groups.

    Args:
        region: AWS region (defaults to Config.AWS_REGION)

    Returns:
        List of discovered Agent objects
    """
    if region is None:
        region = Config.AWS_REGION

    logs_client = boto3.client("logs", region_name=region)

    # Query runtime log groups
    response = logs_client.describe_log_groups(logGroupNamePrefix=Config.RUNTIME_LOG_PREFIX)

    agents = []
    for log_group in response.get("logGroups", []):
        name = extract_runtime_name(log_group["logGroupName"])

        # Get last activity timestamp (creation time or last event time)
        last_activity_ms = log_group.get("creationTime", 0)

        agents.append(
            Agent(
                name=name,
                log_group=log_group["logGroupName"],
                last_activity=datetime.fromtimestamp(last_activity_ms / 1000),
            )
        )

    return agents
