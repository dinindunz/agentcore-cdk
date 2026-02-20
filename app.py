from dotenv import load_dotenv

import aws_cdk as cdk

from src.cdk import AgentCoreStack

load_dotenv()


app = cdk.App()

# Get environment from context (e.g., cdk deploy -c env=dev)
# Defaults to "dev" if not specified
env = app.node.try_get_context("env") or "dev"

AgentCoreStack(
    app,
    f"AgentCoreStack-{env}",
)

app.synth()
