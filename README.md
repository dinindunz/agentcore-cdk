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

Invoke the Agent runtime:

```bash
python scripts/agent/invoke_agent.py
```

## Gateway Tool Search

Semantically search for tools across all gateway targets using the `x_amz_bedrock_agentcore_search` built-in. Returns the most relevant tools ranked by semantic similarity. Accepts an optional query argument:

```bash
# Search via JWT gateway (Cognito auth)
python scripts/gateway/search_tools_jwt.py "find calculator tools"

# Search via IAM gateway (SigV4 auth)
python scripts/gateway/search_tools_iam.py "convert temperature"
```