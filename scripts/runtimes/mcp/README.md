# MCP Runtime Scripts

Scripts for directly invoking MCP runtimes on AgentCore using Cognito JWT authentication.

## Overview

MCP runtimes are containerized MCP servers deployed on AgentCore. These scripts invoke them directly using:
- **Authentication**: Cognito OAuth2 client_credentials flow
- **Endpoint**: `https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{runtime_arn}/invocations`

## Available Scripts

### MCP Server Tests
- **`invoke_calculator.py`** - Test calculator MCP runtime (add tool)

### Examples

```bash
# Test calculator runtime
python invoke_calculator.py
```

## Configuration

Requires the following environment variables (via `.env`):
- `REGION_NAME` - AWS region (e.g., ap-southeast-2)

Requires the following AWS resources:
- SSM Parameter: `/agent-core-stack-dev/mcp-calculator-runtime-arn`
- Secrets Manager Secret: `agent-core-stack-dev/mcp-cognito` containing:
  - `client_id` - Cognito app client ID
  - `client_secret` - Cognito app client secret
  - `token_endpoint` - Cognito OAuth2 token endpoint
  - `user_pool_id` - Cognito user pool ID

## How It Works

1. **Authenticate** - Get OAuth2 access token from Cognito using client_credentials grant
2. **Invoke Runtime** - Send MCP JSON-RPC request with Bearer token to runtime endpoint
3. **Process Response** - Handle MCP protocol response

## Adding New Runtime Tests

To test a new MCP runtime:

1. Deploy the runtime to AgentCore
2. Store the runtime ARN in SSM (e.g., `/agent-core-stack-dev/{name}-runtime-arn`)
3. Create a new script following the `invoke_calculator.py` pattern
4. Update this README
