"""MCP client setup and tool aggregation.

This module provides functionality for creating and managing MCP clients that
connect to AgentCore gateways with different authentication methods (JWT/Cognito
and IAM/SigV4), and for loading and deduplicating tools from multiple sources.
"""

from collections.abc import Sequence
from typing import Any

from auth.cognito import get_access_token
from auth.sigv4 import SigV4Auth
from strands.tools.mcp import MCPClient

from common.logger import logger
from config import AgentConfig

# TODO: Refactor to use streamable_http_client
from mcp.client.streamable_http import streamablehttp_client


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
    logger.debug(f"[Gateway] Creating JWT transport: url={config.jwt_gateway_url}")

    # Fetch a fresh token on each connection to handle expiry in long-running containers
    token = get_access_token(config.gateway_cognito)

    logger.debug(f"[Gateway] JWT transport created: token_length={len(token)}")
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
    logger.debug(f"[Gateway] Creating IAM transport: url={config.iam_gateway_url}")

    transport = streamablehttp_client(
        config.iam_gateway_url,
        auth=sigv4_auth,
    )

    logger.debug("[Gateway] IAM transport created with SigV4 auth")
    return transport


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
    """
    logger.info("[Gateway] Setting up MCP clients")

    # Create JWT-authenticated client with transport factory
    logger.debug("[Gateway] Initialising JWT MCP client")
    jwt_client = MCPClient(lambda: create_jwt_transport(config))
    jwt_client.__enter__()
    logger.debug("[Gateway] JWT MCP client ready")

    # Create IAM-authenticated client with transport factory
    logger.debug("[Gateway] Initialising IAM MCP client")
    iam_client = MCPClient(lambda: create_iam_transport(config, sigv4_auth))
    iam_client.__enter__()
    logger.debug("[Gateway] IAM MCP client ready")

    logger.info("[Gateway] MCP clients setup complete")
    return jwt_client, iam_client


def load_all_tools(jwt_client: MCPClient, iam_client: MCPClient) -> Sequence[Any]:
    """
    Load and deduplicate tools from multiple MCP clients.

    Aggregates tools from both JWT and IAM gateways. When duplicate tool names
    are encountered (e.g., x_amz_bedrock_agentcore_search exposed by both
    gateways), only the first occurrence is kept to avoid naming conflicts.

    Current behaviour: JWT gateway tools are prioritised over IAM gateway tools.
    Duplicate tools from the IAM gateway are silently dropped.

    Args:
        jwt_client: JWT-authenticated MCP client
        iam_client: IAM-authenticated MCP client

    Returns:
        Deduplicated list of tools from all clients

    TODO:
        Improve deduplication strategy to merge tools intelligently rather than
        silently dropping duplicates. Consider tool metadata, capabilities, or
        explicit priority configuration.
    """
    logger.info("[Gateway] Loading tools from MCP clients")

    # Load tools from JWT gateway
    jwt_tools = jwt_client.list_tools_sync()
    logger.debug(f"[Gateway] JWT gateway tools: count={len(jwt_tools)}")
    for tool in jwt_tools:
        logger.debug(f"[Gateway] JWT tool: name={tool.tool_name}")

    # Load tools from IAM gateway
    iam_tools = iam_client.list_tools_sync()
    logger.debug(f"[Gateway] IAM gateway tools: count={len(iam_tools)}")
    for tool in iam_tools:
        logger.debug(f"[Gateway] IAM tool: name={tool.tool_name}")

    # Deduplicate tools
    seen_tool_names: set[str] = set()
    tools = []
    duplicates = []

    for tool in jwt_tools + iam_tools:
        if tool.tool_name not in seen_tool_names:
            seen_tool_names.add(tool.tool_name)
            tools.append(tool)
        else:
            duplicates.append(tool.tool_name)

    if duplicates:
        logger.debug(f"[Gateway] Duplicate tools skipped: {duplicates}")

    logger.info(f"[Gateway] Tools loaded: total={len(tools)} duplicates_removed={len(duplicates)}")
    return tools
