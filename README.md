# AgentCore CDK

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

## Deployment

Deploy from the project root, specifying the `env` context parameter:

```bash
# Deploy to dev environment (default)
cdk deploy

# Or explicitly specify dev
cdk deploy -c env=dev

# Deploy to test environment
cdk deploy -c env=test

# Deploy to prod environment
cdk deploy -c env=prod
```

## Invoking

Invoke the MCP Calculator runtime directly:

```bash
python scripts/mcp/calculator/invoke_direct.py
```

Invoke the MCP Calculator via the IAM gateway:

```bash
python scripts/mcp/calculator/invoke_via_iam_gateway.py
```

Invoke the Temperature Converter via the JWT gateway:

```bash
python scripts/mcp/temperature_converter/invoke_via_jwt_gateway.py
```

Invoke the GitHub API tools via the JWT gateway:

```bash
python scripts/mcp/github/invoke_via_jwt_gateway.py
```

Invoke the Agent runtime:

```bash
python scripts/agent/invoke_agent.py
```

## Gateway Tools

List all available tools on a gateway:

```bash
# List via IAM gateway (SigV4 auth)
python scripts/gateways/iam/list_tools.py

# List via JWT gateway (Cognito auth)
python scripts/gateways/jwt/list_tools.py
```

Semantically search for tools across all gateway targets using the `x_amz_bedrock_agentcore_search` built-in. Returns the most relevant tools ranked by semantic similarity. Accepts an optional query argument:

```bash
# Search via IAM gateway (SigV4 auth)
python scripts/gateways/iam/search_tools.py "convert temperature"

# Search via JWT gateway (Cognito auth)
python scripts/gateways/jwt/search_tools.py "find calculator tools"
```