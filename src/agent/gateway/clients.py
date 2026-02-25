"""MCP client setup and tool aggregation.

This module provides functionality for creating and managing MCP clients that
connect to AgentCore gateways with different authentication methods (JWT/Cognito
and IAM/SigV4), and for loading and deduplicating tools from multiple sources.

Example:
    from config import get_config
    from gateway.clients import setup_mcp_clients, load_all_tools

    config = get_config()
    jwt_client, iam_client = setup_mcp_clients(config)
    tools = load_all_tools(jwt_client, iam_client)
"""

from collections.abc import Sequence
from typing import Any

from strands.tools.mcp import MCPClient

# TODO: Refactor to use streamable_http_client
from mcp.client.streamable_http import streamablehttp_client

from ..auth.cognito import get_access_token
from ..auth.sigv4 import SigV4Auth
from ..config import AgentConfig


def create_jwt_transport(config: AgentConfig) -> Any:
    """
    Create streamable HTTP transport with Cognito JWT authentication.

    Fetches a fresh OAuth2 access token on each connection to handle token
    expiry in long-running containers.

    Args:
        config: Agent configuration with gateway URL and Cognito credentials

    Returns:
        Streamable HTTP transport instance configured with JWT authentication

    Raises:
        httpx.HTTPStatusError: If token request fails
        KeyError: If required configuration is missing
    """
    # Fetch a fresh token on each connection to handle expiry in long-running containers
    token = get_access_token(config.gateway_cognito)
    return streamablehttp_client(
        config.jwt_gateway_url,
        headers={"Authorization": f"Bearer {token}"},
    )


def create_iam_transport(config: AgentConfig, sigv4_auth: SigV4Auth) -> Any:
    """
    Create streamable HTTP transport with AWS IAM SigV4 authentication.

    Args:
        config: Agent configuration with gateway URL
        sigv4_auth: SigV4 authentication instance for signing requests

    Returns:
        Streamable HTTP transport instance configured with SigV4 authentication
    """
    return streamablehttp_client(
        config.iam_gateway_url,
        auth=sigv4_auth,
    )


def setup_mcp_clients(config: AgentConfig, sigv4_auth: SigV4Auth) -> tuple[MCPClient, MCPClient]:
    """
    Initialise JWT and IAM MCP clients.

    Creates and enters context managers for both MCP clients. The clients remain
    active for the lifetime of the agent runtime.

    Args:
        config: Agent configuration with gateway URLs and credentials
        sigv4_auth: SigV4 authentication instance for IAM gateway

    Returns:
        Tuple of (jwt_client, iam_client), both initialised and ready to use

    Example:
        config = get_config()
        auth = SigV4Auth(region=config.region_name)
        jwt_client, iam_client = setup_mcp_clients(config, auth)

        # Clients are now ready to list and call tools
        tools = jwt_client.list_tools_sync()
    """
    # Create JWT-authenticated client with transport factory
    jwt_client = MCPClient(lambda: create_jwt_transport(config))
    jwt_client.__enter__()

    # Create IAM-authenticated client with transport factory
    iam_client = MCPClient(lambda: create_iam_transport(config, sigv4_auth))
    iam_client.__enter__()

    return jwt_client, iam_client


def load_all_tools(jwt_client: MCPClient, iam_client: MCPClient) -> Sequence[Any]:
    """
    Load and deduplicate tools from multiple MCP clients.

    Aggregates tools from both JWT and IAM gateways, handling duplicate tool
    names by keeping only the first occurrence. This is necessary because both
    gateways may expose tools with identical names (e.g., the built-in
    x_amz_bedrock_agentcore_search tool).

    Args:
        jwt_client: JWT-authenticated MCP client
        iam_client: IAM-authenticated MCP client

    Returns:
        Deduplicated list of tools from all clients

    Note:
        Both gateways may expose tools with identical names (e.g.,
        x_amz_bedrock_agentcore_search). Only the first encountered
        tool is kept to avoid naming conflicts in the agent.

    Example:
        tools = load_all_tools(jwt_client, iam_client)
        print(f"Loaded {len(tools)} unique tools")

        for tool in tools:
            print(f"  - {tool.tool_name}")
    """
    # TODO: Improve deduplication strategy - currently silently drops duplicate tools from IAM gateway
    seen_tool_names: set[str] = set()
    tools = []

    for tool in jwt_client.list_tools_sync() + iam_client.list_tools_sync():
        if tool.tool_name not in seen_tool_names:
            seen_tool_names.add(tool.tool_name)
            tools.append(tool)

    return tools
