from dotenv import load_dotenv

import aws_cdk as cdk

from src.cdk import AgentCoreStack, ObservabilityStack

load_dotenv()


app = cdk.App()

# Get environment from context (e.g., cdk deploy -c env=dev)
# Defaults to "dev" if not specified
env = app.node.try_get_context("env") or "dev"

# Deploy observability stack (Arize Phoenix + OpenTelemetry)
# Enable with: cdk deploy -c observability=true
if app.node.try_get_context("observability"):
    ObservabilityStack(
        app,
        f"ObservabilityStack-{env}",
    )

AgentCoreStack(
    app,
    f"AgentCoreStack-{env}",
)

app.synth()
