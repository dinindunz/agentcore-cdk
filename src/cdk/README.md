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

**Note**: When using direct CDK commands for ObservabilityStack, remember to run the Phoenix project creation script manually afterward (see below).

### Stack Names

Stacks follow the naming pattern: `{StackType}-{env}`

- **ObservabilityStack-dev** (default) - Phoenix and OpenTelemetry Collector
- **AgentCoreStack-dev** (default) - Gateways, runtimes, and MCP servers

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
