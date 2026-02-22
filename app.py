from dotenv import load_dotenv

import aws_cdk as cdk

from src.cdk import AgentCoreStack, ObservabilityStack

load_dotenv()

app = cdk.App()

# Environment: dev, test, or prod
env = app.node.try_get_context("env")

# Observability Stack: Arize Phoenix + OpenTelemetry
observability_stack = ObservabilityStack(
    app,
    f"ObservabilityStack-{env}",
)

# AgentCore Stack: Gateways, Runtimes, MCP Servers
agent_stack = AgentCoreStack(
    app,
    f"AgentCoreStack-{env}",
    observability_stack=observability_stack,
)

# Ensure ObservabilityStack deploys before AgentCoreStack
agent_stack.add_dependency(observability_stack)

app.synth()
