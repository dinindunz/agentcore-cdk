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

### Direct CDK Commands

You can also use CDK commands directly with stack names:

```bash
# Deploy both stacks to dev environment (default)
cdk deploy --all

# Deploy both stacks to production
cdk deploy --all -c env=prod

# Deploy only AgentCore stack
cdk deploy AgentCoreStack-dev

# Deploy only Observability stack
cdk deploy ObservabilityStack-dev

# Deploy production stack
cdk deploy AgentCoreStack-prod -c env=prod

# View changes before deploying
cdk diff --all

# Destroy both stacks
cdk destroy --all
```

**Note**: When using direct CDK commands for ObservabilityStack, remember to run the Phoenix project creation script manually afterward (see below).

### Stack Names

Stacks follow the naming pattern: `{StackType}-{env}`

- **ObservabilityStack-dev** (default) - Phoenix and OpenTelemetry Collector
- **AgentCoreStack-dev** (default) - Gateways, runtimes, and MCP servers
- **ObservabilityStack-prod** - Production observability stack
- **AgentCoreStack-prod** - Production agent stack

## Environment Context

The `env` context parameter controls resource naming and configuration:
- **dev** (default) - Development environment
- **test** - Testing environment
- **prod** - Production environment

All resource names are prefixed with the stack name (e.g., `observabilitystack-dev-*`, `agentcorestack-dev-*`).

## Deployment Order

When deploying both stacks (using `--all`), they automatically deploy in the correct order:
1. **ObservabilityStack-{env}** - Phoenix and OTEL Collector
2. **AgentCoreStack-{env}** - Agent runtime (with Phoenix integration)

The agent stack automatically detects and integrates with the observability stack when both are deployed.

## Phoenix Project Creation

The ObservabilityStack deployment script (`./scripts/deploy/observability.sh`) automatically creates the Phoenix project after deployment.

If you deploy manually using `cdk deploy`, create the Phoenix project afterward:

```bash
# Create Phoenix project (default: agentcore-stack-dev)
python scripts/observability/create_phoenix_project.py

# Create with custom parameters
python scripts/observability/create_phoenix_project.py \
  --stack-name ObservabilityStack-prod \
  --project-name agentcore-stack-prod \
  --region ap-southeast-2
```

**Note**: Phoenix projects are created automatically when the agent sends its first trace. The script pre-creates the project namespace for organizational clarity, but it's optional.
