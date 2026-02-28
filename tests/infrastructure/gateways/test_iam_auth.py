"""Infrastructure tests for IAM gateway authentication (SigV4)."""

import pytest

from tests.common.auth import iam as auth


@pytest.mark.infrastructure
def test_iam_gateway_sigv4_auth_success(iam_gateway_url):
    """Test successful SigV4 authentication and request."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    status_code, response = auth.make_request(payload)

    assert status_code == 200, f"Expected 200, got {status_code}: {response}"
    assert "result" in response, "Response missing 'result' field"
    assert "tools" in response["result"], "Response missing 'tools' in result"


@pytest.mark.infrastructure
def test_iam_gateway_list_tools(iam_gateway_url):
    """Test listing tools returns expected structure."""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }

    status_code, response = auth.make_request(payload)

    assert status_code == 200
    assert isinstance(response["result"]["tools"], list)
    assert len(response["result"]["tools"]) > 0, "No tools found in gateway"

    # Verify tool structure
    tool = response["result"]["tools"][0]
    assert "name" in tool
    assert "inputSchema" in tool
