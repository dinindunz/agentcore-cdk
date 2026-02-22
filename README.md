# AgentCore CDK

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

## Deployment

```bash
# Deploy to dev (default)
cdk deploy

# Deploy to specific environment
cdk deploy -c env=prod
```

For detailed deployment options and infrastructure documentation, see **[CDK Infrastructure](src/cdk/README.md)**.

## Scripts

Detailed documentation for each script category:

### Gateways
- **[IAM Gateway](scripts/gateways/iam/README.md)** - SigV4-authenticated gateway scripts (list, search, invoke tools)
- **[JWT Gateway](scripts/gateways/jwt/README.md)** - Cognito JWT-authenticated gateway scripts (list, search, invoke tools)

### Runtimes
- **[Agent Runtime](scripts/runtimes/agent/README.md)** - Agent orchestration scripts and skill tests
- **[MCP Runtime](scripts/runtimes/mcp/README.md)** - Direct MCP runtime invocation scripts