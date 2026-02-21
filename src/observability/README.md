# Observability Stack - Arize Phoenix & OpenTelemetry

This stack deploys Arize Phoenix for AI observability and an OpenTelemetry Collector for trace/metric collection on AWS using ECS Fargate.

## Architecture

- **VPC**: Single availability zone with public subnet only (simplified for observability)
- **Arize Phoenix**: Deployed on ECS Fargate with Application Load Balancer
- **OpenTelemetry Collector**: Deployed on ECS Fargate for receiving OTLP traces
- **Secrets Manager**: Stores Phoenix API key for authentication

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS CDK installed (`npm install -g aws-cdk`)
3. Python dependencies installed (`pip install -r requirements.txt`)

### Deploy the Stack

```bash
# Deploy observability stack
cdk deploy ObservabilityStack-dev -c observability=true

# Or specify a different environment
cdk deploy ObservabilityStack-prod -c env=prod -c observability=true
```

### Outputs

After deployment, you'll receive:

- **PhoenixUrl**: URL to access the Arize Phoenix dashboard
- **OtelCollectorEndpointHttp**: HTTP endpoint for sending OTLP data
- **PhoenixApiKeySecretArn**: ARN of the API key secret in Secrets Manager

## Configuration

### Retrieve Phoenix API Key

```bash
# Get the API key from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id <stack-name>/phoenix-api-key \
  --query SecretString \
  --output text | jq -r '.api_key'
```

### Configure Your Agent to Send Traces

Add the following environment variables to your agent configuration:

```bash
# OpenTelemetry configuration
export OTEL_EXPORTER_OTLP_ENDPOINT="<OtelCollectorEndpointHttp>"
export OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
export OTEL_SERVICE_NAME="your-agent-service"

# Phoenix configuration (if instrumenting directly)
export PHOENIX_COLLECTOR_ENDPOINT="<PhoenixUrl>"
export PHOENIX_API_KEY="<retrieved-from-secrets-manager>"
```

### Python Example

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="<OtelCollectorEndpointHttp>/v1/traces",
)

# Set up tracer
provider = TracerProvider()
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Use tracer in your code
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("agent_execution"):
    # Your agent code here
    pass
```

## Resource Specifications

### Phoenix Service
- **CPU**: 512 (0.5 vCPU)
- **Memory**: 1024 MB
- **Container**: `arizephoenix/phoenix:latest`
- **Port**: 6006 (mapped to ALB port 80)

### OpenTelemetry Collector
- **CPU**: 256 (0.25 vCPU)
- **Memory**: 512 MB
- **Container**: `otel/opentelemetry-collector-contrib:latest`
- **Ports**: 4317 (gRPC), 4318 (HTTP)

## Cost Estimation

Approximate monthly costs (us-east-1):

- **Fargate**: ~$30-40/month (2 tasks running 24/7)
- **Application Load Balancers**: ~$32/month (2 ALBs)
- **Network Transfer**: Variable based on traffic
- **CloudWatch Logs**: ~$5-10/month

**Total**: ~$70-85/month

## Security

- Phoenix API key is automatically generated and stored in AWS Secrets Manager
- Security groups restrict traffic to necessary ports only
- All services run in public subnets with appropriate security group rules
- Consider adding VPN/SSO for production deployments

## Customization

### Adjust Resource Limits

Edit `src/cdk/stacks/observability.py`:

```python
# Phoenix task definition
phoenix_task_def = ecs.FargateTaskDefinition(
    self,
    "PhoenixTaskDef",
    family=f"{stack_prefix}-phoenix",
    cpu=1024,  # Increase CPU
    memory_limit_mib=2048,  # Increase memory
)
```

### Add Private Subnets

For production, you may want to add private subnets:

```python
self._vpc = ec2.Vpc(
    self,
    "Vpc",
    max_azs=2,  # Multiple AZs
    nat_gateways=1,  # Add NAT gateway
    subnet_configuration=[
        ec2.SubnetConfiguration(
            name="Public",
            subnet_type=ec2.SubnetType.PUBLIC,
            cidr_mask=24,
        ),
        ec2.SubnetConfiguration(
            name="Private",
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            cidr_mask=24,
        ),
    ],
)
```

## Monitoring

The stack includes:

- **CloudWatch Container Insights**: Enabled on the ECS cluster
- **CloudWatch Logs**: 7-day retention for all containers
- **Health Checks**: Configured for both services

### View Logs

```bash
# Phoenix logs
aws logs tail /aws/ecs/<stack-name>-phoenix --follow

# OpenTelemetry Collector logs
aws logs tail /aws/ecs/<stack-name>-otel-collector --follow
```

## Troubleshooting

### Phoenix Container Not Starting

Check CloudWatch Logs:
```bash
aws logs tail /aws/ecs/<stack-name>-phoenix --follow
```

### OTLP Data Not Appearing in Phoenix

1. Verify OpenTelemetry Collector is running
2. Check that the Phoenix endpoint is reachable from the collector
3. Verify your agent is sending data to the correct OTLP endpoint

### Load Balancer Health Checks Failing

Check security group rules and ensure:
- Phoenix port 6006 is accessible
- OTLP ports 4317/4318 are accessible
- Target groups are configured correctly

## Clean Up

To remove all resources:

```bash
cdk destroy ObservabilityStack-dev -c observability=true
```

## References

- [Arize Phoenix Documentation](https://docs.arize.com/phoenix)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [AWS ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)