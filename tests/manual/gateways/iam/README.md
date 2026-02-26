# IAM Gateway Scripts

Scripts for interacting with IAM-authenticated AgentCore gateways using AWS SigV4 signing.

## Authentication Module

The `auth.py` module provides reusable authentication functions:

### Functions

- **`get_gateway_url()`** - Fetch the IAM gateway URL from SSM
- **`get_credentials()`** - Get AWS credentials for SigV4 signing
- **`get_signed_headers(url, payload, include_event_stream=True)`** - Get SigV4 signed headers
- **`make_request(payload, include_event_stream=True)`** - Make authenticated SigV4-signed request

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

status_code, response_data = auth.make_request(payload)
if status_code == 200:
    print(json.dumps(response_data, indent=2))
else:
    print(f"Error: {response_data}")
```

## Available Scripts

### Gateway Operations
- **`list_tools.py`** - List all available tools
- **`search_tools.py`** - Semantically search for tools across all gateway targets using the `x_amz_bedrock_agentcore_search` built-in. Returns the most relevant tools ranked by semantic similarity.
- **`invoke_tool.py`** - Invoke a specific tool (generic): `python invoke_tool.py calculator___add '{"a": 5, "b": 3}'`

### Run comprehensive MCP server tests (multiple operations)
- **`mcp_tests/calculator.py`** - Test calculator MCP server (add tool)
- **`mcp_tests/skill_search.py`** - Test skill search MCP server

## Configuration

Requires the following environment variables (via `.env`):
- `REGION_NAME` - AWS region (e.g., ap-southeast-2)

Requires the following AWS resources:
- SSM Parameter: `/agent-core-stack-dev/iam-gateway-url`

Requires valid AWS credentials in the environment (via AWS CLI profile, environment variables, or IAM role).
