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

## Scripts

Detailed documentation for each script category:

### Gateways
- **[IAM Gateway](scripts/gateways/iam/README.md)** - SigV4-authenticated gateway scripts (list, search, invoke tools)
- **[JWT Gateway](scripts/gateways/jwt/README.md)** - Cognito JWT-authenticated gateway scripts (list, search, invoke tools)

### Runtimes
- **[Agent Runtime](scripts/runtimes/agent/README.md)** - Agent orchestration scripts and skill tests
- **[MCP Runtime](scripts/runtimes/mcp/README.md)** - Direct MCP runtime invocation scripts