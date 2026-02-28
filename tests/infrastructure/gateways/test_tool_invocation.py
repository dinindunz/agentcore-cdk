"""Infrastructure tests for end-to-end tool invocation through gateways."""

import pytest

from tests.common.auth import iam as iam_auth
from tests.common.auth import jwt as jwt_auth


@pytest.mark.infrastructure
def test_iam_gateway_invoke_calculator_add():
    """Test invoking calculator add tool via IAM gateway."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "calculator___add",
            "arguments": {"a": 5, "b": 3},
        },
    }

    status_code, response = iam_auth.make_request(payload)

    assert status_code == 200, f"Expected 200, got {status_code}: {response}"
    assert "result" in response
    assert response["result"]["content"][0]["text"] == "8"


@pytest.mark.infrastructure
def test_jwt_gateway_invoke_temperature_converter():
    """Test invoking temperature converter via JWT gateway."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "temperature-converter___celsius_to_fahrenheit",
            "arguments": {"celsius": 0},
        },
    }

    response = jwt_auth.make_request(payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "result" in data
    # 0°C = 32°F
    assert "32" in data["result"]["content"][0]["text"]


@pytest.mark.infrastructure
def test_iam_gateway_search_tools():
    """Test semantic tool search via IAM gateway."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "x_amz_bedrock_agentcore_search",
        "params": {
            "query": "arithmetic operations",
            "maxResults": 5,
        },
    }

    status_code, response = iam_auth.make_request(payload)

    assert status_code == 200
    assert "result" in response
    assert "tools" in response["result"]
    assert isinstance(response["result"]["tools"], list)
    # Should find calculator tools
    tool_names = [t["name"] for t in response["result"]["tools"]]
    assert any("calculator" in name for name in tool_names)
