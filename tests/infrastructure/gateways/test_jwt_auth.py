"""Infrastructure tests for JWT gateway authentication (Cognito OAuth2)."""

import pytest

from tests.common.auth import jwt as auth


@pytest.mark.infrastructure
def test_jwt_gateway_oauth2_auth_success(jwt_gateway_url):
    """Test successful OAuth2 token acquisition and request."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    response = auth.make_request(payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "result" in data, "Response missing 'result' field"
    assert "tools" in data["result"], "Response missing 'tools' in result"


@pytest.mark.infrastructure
def test_jwt_gateway_list_tools(jwt_gateway_url):
    """Test listing tools returns expected structure."""
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }

    response = auth.make_request(payload)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["result"]["tools"], list)
    assert len(data["result"]["tools"]) > 0, "No tools found in gateway"

    # Verify tool structure
    tool = data["result"]["tools"][0]
    assert "name" in tool
    assert "inputSchema" in tool


@pytest.mark.infrastructure
def test_jwt_token_caching():
    """Test that token acquisition is cached and reused."""
    # Get token twice - second call should be cached
    token1 = auth.get_access_token()
    token2 = auth.get_access_token()

    assert token1 == token2, "Tokens should be identical"
    # Tokens should be valid (non-empty strings)
    assert token1 is not None and len(token1) > 0
