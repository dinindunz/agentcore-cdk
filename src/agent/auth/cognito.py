"""OAuth2 authentication for Cognito-protected gateways.

This module provides functionality to obtain OAuth2 access tokens using the
client_credentials flow for authenticating with Cognito-protected AgentCore
gateways.

Example:
    from auth.cognito import get_access_token
    from config import get_config

    config = get_config()
    token = get_access_token(config.gateway_cognito)
    # Use token in Authorization header
"""

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ..config import GatewayCognitoConfig


def get_access_token(config: "GatewayCognitoConfig") -> str:
    """
    Get an OAuth2 access token using client_credentials flow.

    Exchanges Cognito client credentials for an access token that can be used
    to authenticate with JWT-protected AgentCore gateways.

    Args:
        config: Cognito configuration with token endpoint and credentials.
            Must contain:
            - token_endpoint: OAuth2 token endpoint URL
            - client_id: Cognito app client ID
            - client_secret: Cognito app client secret

    Returns:
        OAuth2 access token string (valid for the duration configured in Cognito)

    Raises:
        httpx.HTTPStatusError: If token request fails (4xx/5xx status)
        httpx.RequestError: If network request fails
        KeyError: If response doesn't contain access_token

    Example:
        try:
            token = get_access_token(cognito_config)
            headers = {"Authorization": f"Bearer {token}"}
        except httpx.HTTPStatusError as e:
            print(f"Failed to get token: {e.response.status_code}")
    """
    response = httpx.post(
        config["token_endpoint"],
        data={
            "grant_type": "client_credentials",
            "scope": "gateway/invoke",
        },
        auth=(config["client_id"], config["client_secret"]),
    )
    response.raise_for_status()
    return response.json()["access_token"]
