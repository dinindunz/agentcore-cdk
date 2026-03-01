"""Authentication modules for AgentCore gateways and runtimes."""

from .iam import get_credentials, get_signed_headers
from .iam import get_gateway_url as get_iam_gateway_url
from .iam import make_request as make_iam_request
from .jwt import get_access_token, get_headers
from .jwt import get_gateway_url as get_jwt_gateway_url
from .jwt import make_request as make_jwt_request

__all__ = [
    # IAM/SigV4 auth
    "get_iam_gateway_url",
    "get_credentials",
    "get_signed_headers",
    "make_iam_request",
    # JWT/OAuth2 auth
    "get_jwt_gateway_url",
    "get_access_token",
    "get_headers",
    "make_jwt_request",
]
