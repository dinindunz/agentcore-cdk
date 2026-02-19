# AgentCore CDK

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Deployment

Deploy to different environments by specifying the `env` context parameter:

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

Invoke the MCP Calculator runtime:

```bash
python invoke_mcp.py
```

Invoke the Agent runtime:

```bash
python invoke_agent.py
```

Invoke the MCP Calculator runtime via the Gateway:

```bash
python invoke_mcp_via_gateway.py
```