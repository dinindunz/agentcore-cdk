"""Gateway client modules for MCP server access.

This package provides functionality for setting up and managing MCP clients
that connect to AgentCore gateways (JWT and IAM authenticated) and aggregating
tools from multiple sources.
"""

from .clients import create_iam_transport, create_jwt_transport, load_all_tools, setup_mcp_clients

__all__ = ["create_jwt_transport", "create_iam_transport", "setup_mcp_clients", "load_all_tools"]
