#!/usr/bin/env python3
import aws_cdk as cdk

from src.cdk import AgentcoreCdkStack


app = cdk.App()

# Get environment from context (e.g., cdk deploy -c env=dev)
# Defaults to "dev" if not specified
env = app.node.try_get_context("env") or "dev"

AgentcoreCdkStack(
    app,
    f"AgentcoreCdkStack-{env}",
)

app.synth()
