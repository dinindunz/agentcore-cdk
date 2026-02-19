# AgentCore CDK

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

## Deployment

CDK files live in `src/cdk/`. Deploy from there, specifying the `env` context parameter:

```bash
cd src/cdk

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

Invoke the MCP Calculator via the JWT gateway:

```bash
python scripts/mcp/calculator/invoke_via_jwt_gateway.py
```

Invoke the Agent runtime:

```bash
python scripts/agent/invoke_agent.py
```