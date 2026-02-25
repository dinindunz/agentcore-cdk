"""Authentication modules for AgentCore gateways.

This package provides authentication mechanisms for different gateway types:
- OAuth2 (Cognito) authentication for JWT-protected gateways
- AWS SigV4 authentication for IAM-protected gateways
"""

from .cognito import get_access_token
from .sigv4 import SigV4Auth

__all__ = ["get_access_token", "SigV4Auth"]
