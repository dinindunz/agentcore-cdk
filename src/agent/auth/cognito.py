"""OAuth2 authentication for Cognito-protected gateways.

This module provides functionality to obtain OAuth2 access tokens using the
client_credentials flow for authenticating with Cognito-protected AgentCore
gateways.
"""

import os
import time
from typing import TYPE_CHECKING

import httpx

from common.logger import logger

if TYPE_CHECKING:
    from ..config import GatewayCognitoConfig

# Token cache: stores (token, expiry_time)
# Module-level cache persists across Lambda invocations in warm containers
_token_cache: tuple[str, float] | None = None

# OAuth token cache buffer configuration (from environment variables)
_BUFFER_PERCENT = float(os.getenv("OAUTH_CACHE_BUFFER_PERCENT", "10.0"))
_BUFFER_MIN_SEC = int(os.getenv("OAUTH_CACHE_BUFFER_MIN_SEC", "60"))
_BUFFER_MAX_SEC = int(os.getenv("OAUTH_CACHE_BUFFER_MAX_SEC", "300"))


def get_access_token(config: "GatewayCognitoConfig") -> str:
    """
    Get an OAuth2 access token using client_credentials flow.

    Exchanges Cognito client credentials for an access token that can be used
    to authenticate with JWT-protected AgentCore gateways.

    Tokens are cached and reused until they expire (with configurable buffer) to
    reduce Cognito API calls, improve performance, and respect service quotas.
    The module-level cache persists across Lambda invocations in warm containers.

    Cache buffer strategy is configured via environment variables:
    - OAUTH_CACHE_BUFFER_PERCENT: Buffer as % of token lifetime (default: 10.0)
    - OAUTH_CACHE_BUFFER_MIN_SEC: Minimum buffer in seconds (default: 60)
    - OAUTH_CACHE_BUFFER_MAX_SEC: Maximum buffer in seconds (default: 300)

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
    """
    global _token_cache

    # Check if we have a valid cached token
    if _token_cache is not None:
        cached_token, expiry_time = _token_cache
        if time.time() < expiry_time:
            logger.debug(
                f"[Auth] Using cached OAuth2 token: client_id={config['client_id']} ttl={int(expiry_time - time.time())}s"
            )
            return cached_token

    logger.debug(f"[Auth] Requesting fresh OAuth2 token: endpoint={config['token_endpoint']}")

    try:
        response = httpx.post(
            config["token_endpoint"],
            data={
                "grant_type": "client_credentials",
                "scope": "gateway/invoke",
            },
            auth=(config["client_id"], config["client_secret"]),
        )
        response.raise_for_status()
        token_data = response.json()
        token = token_data["access_token"]

        # Cache the token with expiry (value from Cognito reflects configured lifetime)
        # Use configurable buffer strategy from environment variables
        expires_in = token_data.get("expires_in", 900)
        buffer_seconds = max(
            _BUFFER_MIN_SEC, min(_BUFFER_MAX_SEC, int(expires_in * _BUFFER_PERCENT / 100.0))
        )
        expiry_time = time.time() + expires_in - buffer_seconds
        _token_cache = (token, expiry_time)

        # Log token metadata (not the actual token for security)
        logger.info(
            f"[Auth] OAuth2 token obtained and cached: length={len(token)} client_id={config['client_id']} expires_in={expires_in}s"
        )
        return token

    except httpx.HTTPStatusError as e:
        logger.error(
            f"[Auth] Token request failed: status={e.response.status_code} endpoint={config['token_endpoint']}"
        )
        raise
    except Exception as e:
        logger.error(f"[Auth] Token request error: {e}")
        raise
