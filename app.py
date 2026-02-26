import os

import aws_cdk as cdk
from dotenv import load_dotenv

from src.cdk import AgentCoreStack
from src.cdk.config import get_config_from_context

load_dotenv()

app = cdk.App()

# Load environment-specific configuration from config/{env}.yaml
config = get_config_from_context(app)

# AWS environment configuration (required for SSM lookups if needed)
aws_env = cdk.Environment(
    account=os.environ.get("AWS_ACCOUNT_ID"),
    region=os.environ.get("REGION_NAME"),
)

# AgentCore Stack: Gateways, Runtimes, MCP Servers
agent_stack = AgentCoreStack(
    app,
    f"AgentCoreStack-{config.environment}",
    config=config,
    env=aws_env,
)

app.synth()
