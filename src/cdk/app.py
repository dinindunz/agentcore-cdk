#!/usr/bin/env python3
import os
import sys

# Add project root to sys.path so src.cdk resolves as a package (enabling relative imports)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

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
