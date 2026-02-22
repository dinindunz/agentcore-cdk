# Phoenix Observability Integration Guide

## Overview

Your agent is now integrated with Arize Phoenix for comprehensive observability and tracing. This guide explains the integration, deployment, and usage.

## What Was Changed

### 1. Agent Dependencies (`src/agent/pyproject.toml`)
Added Phoenix instrumentation packages:
- `arize-phoenix-otel==0.14.0` - Phoenix OpenTelemetry integration
- `openinference-instrumentation-bedrock==0.1.32` - Bedrock-specific instrumentation
- `openinference-instrumentation>=0.1.38` - Base instrumentation library (flexible version to satisfy phoenix-otel)

### 2. Agent Code (`src/agent/main.py`)
Added Phoenix tracing:
- Automatic tracer initialization when `OTEL_EXPORTER_OTLP_ENDPOINT` is set
- Wraps agent execution in trace spans with input/output attributes
- Gracefully degrades when observability is not configured

### 3. CDK Infrastructure

#### ObservabilityStack (`src/cdk/stacks/observability.py`)
- Exposed `otel_endpoint` property for cross-stack references
- Exposed `phoenix_api_key_secret` property for agent access

#### AgentCoreStack (`src/cdk/stacks/agentcore.py`)
- Accepts optional `observability_stack` parameter
- Automatically configures OTEL environment variables when observability is enabled
- Grants agent runtime permission to read Phoenix API key

#### App Configuration (`app.py`)
- Links ObservabilityStack with AgentCoreStack when both are deployed

## Deployment

### Important: Deployment Consistency

**CRITICAL**: Once you deploy with observability enabled, you should continue using the `-c observability=true` flag for all subsequent deployments. Switching between enabled/disabled states can cause stack drift.

```bash
# ✅ Good: Consistent flag usage
cdk deploy --all -c observability=true
cdk deploy --all -c observability=true  # subsequent deploy

# ❌ Bad: Inconsistent flag usage (causes drift)
cdk deploy --all -c observability=true
cdk deploy --all  # observability=false (default) - causes issues!
```

### Step 1: Deploy Observability Stack (if not already deployed)

```bash
# Activate virtual environment
source .venv/bin/activate

# Deploy the observability stack
cdk deploy ObservabilityStack-dev -c observability=true

# Save the outputs (you'll need these)
# - PhoenixUrl: Dashboard URL
# - OtelCollectorEndpointHttp: Trace ingestion endpoint
# - PhoenixApiKeySecretArn: API key secret ARN
```

### Step 2: Deploy AgentCore Stack with Observability

```bash
# Deploy both stacks together (recommended)
cdk deploy --all -c observability=true

# Or deploy just AgentCore if observability is already deployed
cdk deploy AgentCoreStack-dev -c observability=true
```

**Note**: CDK automatically creates a dependency between the stacks, so ObservabilityStack will always deploy before AgentCoreStack.

### Step 3: Verify Integration

```bash
# Check agent runtime logs for Phoenix initialization
aws logs tail /aws/bedrock-agentcore/runtimes/agent_core_stack_dev_agent --follow

# You should see OpenTelemetry initialization messages
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent Execution                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Phoenix OTEL Instrumentation                      │     │
│  │  - Traces agent execution                          │     │
│  │  - Captures input/output                           │     │
│  │  - Records tool calls                              │     │
│  └────────────────┬───────────────────────────────────┘     │
└────────────────────┼────────────────────────────────────────┘
                     │ OTLP/HTTP (port 4318)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector                         │
│  - Receives traces via OTLP                                  │
│  - Forwards to Phoenix                                       │
│  - Public ALB endpoint                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Arize Phoenix                               │
│  - Stores and analyzes traces                                │
│  - Web dashboard (port 6006)                                 │
│  - Public ALB endpoint                                       │
└─────────────────────────────────────────────────────────────┘
```

## Environment Variables (Automatically Configured)

When observability is enabled, the agent runtime receives:

- `OTEL_EXPORTER_OTLP_ENDPOINT`: HTTP endpoint for OpenTelemetry Collector
- `OTEL_EXPORTER_OTLP_PROTOCOL`: Set to `http/protobuf`
- `OTEL_SERVICE_NAME`: Service name for trace identification (e.g., `agentcore-stack-dev-agent`)

## Viewing Traces

### Access Phoenix Dashboard

1. Get the Phoenix URL from CDK outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name ObservabilityStack-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`PhoenixUrl`].OutputValue' \
  --output text
```

2. Open the URL in your browser

3. Navigate to the "Traces" section to see agent executions

### Trace Information

Each agent execution creates a span with:
- **Span Name**: `agent_execution`
- **Attributes**:
  - `input.value`: User's prompt/message
  - `input.mime_type`: `text/plain`
  - `output.value`: Agent's response
  - `output.mime_type`: `text/plain`

## Testing the Integration

### Invoke the Agent

Use the existing agent invocation script:

```bash
cd scripts/runtimes/agent
python invoke_agent.py
```

### Check Traces in Phoenix

1. Open Phoenix dashboard
2. Navigate to "Traces"
3. You should see new traces appearing with your agent invocations
4. Click on a trace to see detailed execution information

## Troubleshooting

### No Traces Appearing

1. **Check agent logs**:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/agent_core_stack_dev_agent --follow
```

2. **Verify OTEL Collector is healthy**:
```bash
# Get OTEL endpoint
OTEL_URL=$(aws cloudformation describe-stacks \
  --stack-name ObservabilityStack-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`OtelCollectorEndpointHttp`].OutputValue' \
  --output text)

# Check health
curl ${OTEL_URL%:*}:13133/
```

3. **Check OTEL Collector logs**:
```bash
aws logs tail /aws/ecs/observabilitystack-dev-otel-collector --follow
```

### Agent Failing to Start

1. **Check if observability environment variables are set**:
```bash
aws bedrock-agentcore get-runtime \
  --runtime-arn <agent-runtime-arn> \
  | jq '.runtime.environmentVariables'
```

2. **Rebuild agent container** (if dependencies changed):
```bash
cdk deploy AgentCoreStack-dev -c observability=true --force
```

### Phoenix Dashboard Not Accessible

1. **Check Phoenix service health**:
```bash
aws logs tail /aws/ecs/observabilitystack-dev-phoenix --follow
```

2. **Verify ALB target health**:
```bash
aws elbv2 describe-target-health \
  --target-group-arn <phoenix-target-group-arn>
```

## Cost Estimation

With observability enabled:

**Existing Costs** (from OBSERVABILITY_DEPLOYMENT.md):
- ECS Fargate: ~$35/month (Phoenix + OTEL Collector)
- Application Load Balancers: ~$32/month (2 ALBs)
- CloudWatch Logs: ~$5-10/month
- Secrets Manager: ~$0.40/month

**Additional Costs**:
- Agent container overhead: Negligible (same Fargate task)
- Data transfer: ~$1-5/month (traces to OTEL Collector)

**Total Additional**: ~$1-5/month

## Disabling Observability

To deploy without observability:

```bash
# Deploy without observability context flag
cdk deploy AgentCoreStack-dev

# This will:
# - Not set OTEL environment variables
# - Agent will skip Phoenix initialization
# - No traces will be sent
```

## Advanced Configuration

### Custom Trace Attributes

Modify `src/agent/main.py` to add custom attributes:

```python
if tracer:
    with tracer.start_as_current_span(
        "agent_execution",
        attributes={
            "input.value": user_message,
            "input.mime_type": "text/plain",
            "custom.user_id": payload.get("user_id", "unknown"),
            "custom.session_id": payload.get("session_id", "unknown"),
        }
    ) as span:
        # ... agent execution ...
        span.set_attribute("custom.tools_used", len(result.tool_calls))
```

### Instrument Tool Calls

Add spans for individual tool executions:

```python
for tool_call in result.tool_calls:
    with tracer.start_as_current_span(
        "tool_execution",
        attributes={
            "tool.name": tool_call.name,
            "tool.input": json.dumps(tool_call.input),
        }
    ) as tool_span:
        # Tool execution happens automatically by strands
        tool_span.set_attribute("tool.output", json.dumps(tool_call.output))
```

## Next Steps

1. **Explore Phoenix Features**:
   - Trace search and filtering
   - Performance analytics
   - Error detection

2. **Set Up Alerts** (future):
   - Configure CloudWatch alarms for trace metrics
   - Set up SNS notifications for errors

3. **Add More Instrumentation**:
   - Instrument gateway calls
   - Add custom metrics
   - Track user sessions

## References

- [Arize Phoenix Documentation](https://docs.arize.com/phoenix)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenInference Specification](https://github.com/Arize-ai/openinference)
