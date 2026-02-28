"""Infrastructure tests for gateway error handling scenarios."""

import pytest

from tests.common.auth import iam as iam_auth
from tests.common.auth import jwt as jwt_auth


@pytest.mark.infrastructure
def test_iam_gateway_invalid_tool_name():
    """Test error handling for non-existent tool."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "nonexistent___tool",
            "arguments": {},
        },
    }

    status_code, response = iam_auth.make_request(payload)

    # Should return error in JSON-RPC format
    assert status_code == 200  # JSON-RPC errors are still HTTP 200
    assert "error" in response, "Expected error in response"


@pytest.mark.infrastructure
def test_jwt_gateway_malformed_arguments():
    """Test error handling for malformed tool arguments."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "temperature-converter___celsius_to_fahrenheit",
            "arguments": {"wrong_param": 25},  # Should be 'celsius'
        },
    }

    response = jwt_auth.make_request(payload)

    # Should return error
    assert response.status_code == 200  # JSON-RPC errors are HTTP 200
    data = response.json()
    assert "error" in data or ("result" in data and "isError" in data["result"])


@pytest.mark.infrastructure
def test_iam_gateway_invalid_method():
    """Test error handling for invalid JSON-RPC method."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "invalid/method",
        "params": {},
    }

    status_code, response = iam_auth.make_request(payload)

    # Should return error
    assert status_code == 200  # JSON-RPC errors are HTTP 200
    assert "error" in response
