# Observability Stack Deployment Guide

## Summary

I've created a new CDK stack for deploying Arize Phoenix and OpenTelemetry Collector on AWS ECS Fargate with a simplified network architecture (single public subnet).

## Files Created/Modified

### New Files:
1. **`src/cdk/stacks/observability.py`** - Main observability stack with:
   - VPC with single public subnet (no NAT gateway for simplicity)
   - ECS Fargate cluster with Container Insights enabled
   - Arize Phoenix service (port 6006) with Application Load Balancer
   - OpenTelemetry Collector service (ports 4317/4318) with Application Load Balancer
   - Auto-generated Phoenix API key stored in AWS Secrets Manager
   - Security groups for controlled access
   - CloudWatch Logs with 7-day retention

2. **`src/observability/README.md`** - Comprehensive documentation including:
   - Architecture overview
   - Deployment instructions
   - Configuration examples
   - Cost estimation (~$70-85/month)
   - Troubleshooting guide

### Modified Files:
1. **`src/cdk/stacks/__init__.py`** - Added ObservabilityStack export
2. **`src/cdk/__init__.py`** - Added ObservabilityStack to main exports
3. **`app.py`** - Added conditional deployment of ObservabilityStack

## Key Features

### Resource Naming
Following your existing naming standards:
- Uses `to_kebab_case()` for resource names (e.g., `agentcore-stack-dev-phoenix`)
- Uses `to_snake_case()` for internal naming
- Stack prefix applied consistently across all resources

### Network Architecture
- **Single AZ, Public Subnet Only**: Simplified deployment without NAT gateway costs
- **No Private Subnets**: All services in public subnet with security groups
- **Security Groups**: Properly configured for Phoenix (6006) and OTLP (4317, 4318)

### Observability Services
1. **Arize Phoenix**:
   - Container: `arizephoenix/phoenix:latest`
   - Resources: 512 CPU, 1024 MB memory
   - Public ALB for dashboard access
   - Auto-generated API key in Secrets Manager

2. **OpenTelemetry Collector**:
   - Container: `otel/opentelemetry-collector-contrib:latest`
   - Resources: 256 CPU, 512 MB memory
   - Supports both gRPC (4317) and HTTP (4318) protocols
   - Public ALB for trace ingestion

## Deployment Instructions

### Prerequisites
```bash
# Activate virtual environment
source .venv/bin/activate

# Ensure dependencies are installed
pip install -r requirements.txt
```

### Deploy Stack
```bash
# Deploy observability stack
cdk deploy ObservabilityStack-dev -c observability=true

# For production environment
cdk deploy ObservabilityStack-prod -c env=prod -c observability=true
```

### Get Outputs
After deployment, CDK will output:
- **PhoenixUrl**: Access the Phoenix dashboard
- **OtelCollectorEndpointHttp**: Send OTLP traces here
- **PhoenixApiKeySecretArn**: Retrieve API key from Secrets Manager

### Retrieve Phoenix API Key
```bash
aws secretsmanager get-secret-value \
  --secret-id observabilitystack-dev/phoenix-api-key \
  --query SecretString \
  --output text | jq -r '.api_key'
```

## Integration with Your Agent

Add OpenTelemetry instrumentation to your agent in `src/agent/main.py`:

```python
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize OpenTelemetry
def setup_telemetry():
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{otlp_endpoint}/v1/traces"
        )
        provider = TracerProvider()
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        
        return trace.get_tracer(__name__)
    return None

# In your agent code
tracer = setup_telemetry()

if tracer:
    with tracer.start_as_current_span("agent_execution"):
        # Your agent logic here
        pass
```

## Environment Variables for Agent

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="<OtelCollectorEndpointHttp>"
export OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
export OTEL_SERVICE_NAME="agentcore-agent"
export PHOENIX_API_KEY="<retrieved-from-secrets-manager>"
```

## Stack Outputs Reference

The stack provides these CloudFormation outputs:

1. **VpcId**: The VPC ID for reference
2. **PublicSubnetIds**: Comma-separated list of public subnet IDs
3. **PhoenixUrl**: Phoenix dashboard URL (http://<alb-dns>)
4. **OtelCollectorEndpointHttp**: OTLP HTTP endpoint (http://<alb-dns>:4318)
5. **PhoenixApiKeySecretArn**: Secret ARN for API key

## Cost Breakdown

Estimated monthly costs (us-east-1):
- **ECS Fargate Tasks**: ~$35/month (2 tasks × 0.5 vCPU average)
- **Application Load Balancers**: ~$32/month (2 ALBs)
- **Data Transfer**: ~$5-10/month (typical agent traffic)
- **CloudWatch Logs**: ~$5/month (7-day retention)
- **Secrets Manager**: ~$0.40/month (1 secret)

**Total**: ~$77-82/month

## Next Steps

1. **Deploy the stack** using the commands above
2. **Verify deployment** by accessing the Phoenix URL
3. **Configure your agent** with the OTLP endpoint
4. **Start sending traces** from your agent
5. **View traces** in the Phoenix dashboard

## Cleanup

To remove all resources:
```bash
cdk destroy ObservabilityStack-dev -c observability=true
```

## Notes

- The stack keeps vpc.py unchanged - you can deploy both VPC stacks independently
- ObservabilityStack is only deployed when `-c observability=true` is passed
- The observability stack is completely self-contained with its own VPC
- All resources follow your existing naming conventions
- Security groups allow public access - consider adding VPN/SSO for production

## Troubleshooting

If you encounter import errors during deployment, ensure:
1. Virtual environment is activated: `source .venv/bin/activate`
2. Dependencies are installed: `pip install -r requirements.txt`
3. Python path is correct: `which python` should point to `.venv/bin/python`

For detailed troubleshooting, see `src/observability/README.md`.