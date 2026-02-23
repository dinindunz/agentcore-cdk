from dotenv import load_dotenv
import os

import aws_cdk as cdk

from src.cdk import AgentCoreStack

load_dotenv()

app = cdk.App()

# Environment: dev, test, or prod
env = app.node.try_get_context("env")

# AWS environment configuration (required for SSM lookups if needed)
aws_env = cdk.Environment(
    account=os.environ.get("AWS_ACCOUNT"),
    region=os.environ.get("REGION_NAME"),
)

# AgentCore Stack: Gateways, Runtimes, MCP Servers
agent_stack = AgentCoreStack(
    app,
    f"AgentCoreStack-{env}",
    env=aws_env,
)

app.synth()
