# CDK Infrastructure

CDK infrastructure for deploying AgentCore resources on AWS.

## Structure

```
src/cdk/
├── stacks/           # CloudFormation stacks
│   ├── agentcore.py     - Main AgentCore stack (gateways, runtimes, MCP servers)
│   └── observability.py - Observability stack (Arize Phoenix, OpenTelemetry)
├── constructs/       # Reusable L3 constructs
│   ├── cognito.py       - Cognito user pools and app clients
│   ├── gateway.py       - AgentCore gateways
│   ├── runtime.py       - AgentCore runtimes
│   ├── identity.py      - Credential providers (OAuth2, API keys)
│   ├── bucket.py        - S3 buckets with lifecycle policies
│   └── gateway_targets/ - Gateway target configurations
└── utils/            # Utility functions
    ├── cleanup.py       - Log group cleanup aspects and custom resources
    └── strings.py       - Case conversion utilities (kebab/PascalCase/snake_case)
```

## Deployment

Deploy from the project root:

```bash
# Deploy to dev (default)
cdk deploy

# Deploy to specific environment
cdk deploy -c env=test
cdk deploy -c env=prod

# Deploy with observability stack
cdk deploy -c observability=true
```

## Environment Context

The `env` context parameter controls resource naming and configuration:
- **dev** (default) - Development environment
- **test** - Testing environment
- **prod** - Production environment

All resource names are prefixed with `agent-core-stack-{env}`.
