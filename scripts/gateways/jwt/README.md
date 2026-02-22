# JWT Gateway Scripts

Scripts for interacting with JWT-authenticated AgentCore gateways using Cognito OAuth2 client_credentials flow.

## Authentication Module

The `auth.py` module provides reusable authentication functions:

### Functions

- **`get_gateway_url()`** - Fetch the JWT gateway URL from SSM
- **`get_access_token()`** - Get OAuth2 access token from Cognito
- **`get_headers(include_event_stream=True)`** - Get authenticated headers
- **`make_request(payload, include_event_stream=True)`** - Make authenticated request

### Usage Example

```python
import json
import auth

# Simple request
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {},
}

response = auth.make_request(payload)
print(response.json())
```

## Available Scripts

### Gateway Operations
- **`list_tools.py`** - List all available tools
- **`search_tools.py`** - Semantically search for tools across all gateway targets using the `x_amz_bedrock_agentcore_search` built-in. Returns the most relevant tools ranked by semantic similarity.
- **`invoke_tool.py`** - Invoke a specific tool (generic)

### MCP Server Tests
- **`mcp_tests/temperature_converter.py`** - Test temperature converter MCP server
- **`mcp_tests/github.py`** - Test GitHub MCP server

### Examples

```bash
# List all tools
python list_tools.py

# Search for tools
python search_tools.py "convert temperature"

# Invoke a tool (generic - single operation)
python invoke_tool.py temperature-converter___celsius_to_fahrenheit '{"celsius": 25}'
python invoke_tool.py github___getAuthenticatedUser '{}'

# Run comprehensive MCP server tests (multiple operations)
python -m mcp_tests.temperature_converter
python -m mcp_tests.github
```

## Configuration

Requires the following environment variables (via `.env`):
- `REGION_NAME` - AWS region (e.g., ap-southeast-2)

Requires the following AWS resources:
- SSM Parameter: `/agent-core-stack-dev/jwt-gateway-url`
- Secrets Manager Secret: `agent-core-stack-dev/gateway-cognito`
