import base64
import urllib.parse

import boto3
import requests
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

REGION_NAME = "ap-southeast-2"

# Fetch config from SSM
ssm_client = boto3.client("ssm", region_name=REGION_NAME)


def get_ssm_param(name):
    return ssm_client.get_parameter(Name=name)["Parameter"]["Value"]


mcp_calculator_arn = get_ssm_param("/agentcore/mcp-calculator-runtime-arn")
cognito_client_id = get_ssm_param("/agentcore/cognito-client-id")
cognito_user_pool_id = get_ssm_param("/agentcore/cognito-user-pool-id")
cognito_token_endpoint = get_ssm_param("/agentcore/cognito-token-endpoint")

# Fetch client secret from Cognito
cognito_client = boto3.client("cognito-idp", region_name=REGION_NAME)
cognito_client_secret = cognito_client.describe_user_pool_client(
    UserPoolId=cognito_user_pool_id,
    ClientId=cognito_client_id,
)["UserPoolClient"]["ClientSecret"]

# Get Cognito access token via client credentials
token_response = requests.post(
    cognito_token_endpoint,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(
            f"{cognito_client_id}:{cognito_client_secret}".encode()
        ).decode(),
    },
    data={
        "grant_type": "client_credentials",
        "scope": "agentcore/invoke",
    },
)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]

# Construct the MCP Calculator invocation URL
escaped_arn = urllib.parse.quote(mcp_calculator_arn, safe="")
mcp_calculator_url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_arn}/invocations?qualifier=DEFAULT"

app = BedrockAgentCoreApp()


def create_mcp_transport():
    return streamablehttp_client(
        mcp_calculator_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )


mcp_client = MCPClient(lambda: create_mcp_transport())
mcp_client.__enter__()

tools = mcp_client.list_tools_sync()
agent = Agent(
    tools=tools,
    system_prompt="You are a helpful assistant. Provide friendly, conversational responses.",
)


@app.entrypoint
def invoke(payload):
    """Process user input and return a response"""
    user_message = payload.get("prompt", "Hello")
    result = agent(user_message)
    text = "".join(
        block["text"] for block in result.message.get("content", []) if "text" in block
    )
    return {"result": text}


app.run()
