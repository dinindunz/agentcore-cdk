import json

import boto3
import httpx
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

REGION_NAME = "ap-southeast-2"

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
sm_client = boto3.client("secretsmanager", region_name=REGION_NAME)

GATEWAY_URL = ssm_client.get_parameter(Name="/agentcore/jwt-gateway-url")["Parameter"][
    "Value"
]

# Fetch Cognito credentials from Secrets Manager
gateway_cognito = json.loads(
    sm_client.get_secret_value(SecretId="agentcore/jwt-gateway-cognito")["SecretString"]
)


def get_access_token() -> str:
    """Get an OAuth2 access token using client_credentials flow."""
    response = httpx.post(
        gateway_cognito["token_endpoint"],
        data={
            "grant_type": "client_credentials",
            "scope": "gateway/invoke",
        },
        auth=(gateway_cognito["client_id"], gateway_cognito["client_secret"]),
    )
    response.raise_for_status()
    return response.json()["access_token"]


access_token = get_access_token()

app = BedrockAgentCoreApp()


def create_mcp_transport():
    return streamablehttp_client(
        GATEWAY_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )


mcp_client = MCPClient(lambda: create_mcp_transport())
mcp_client.__enter__()

tools = mcp_client.list_tools_sync()
agent = Agent(
    tools=tools,
    system_prompt="You are a helpful assistant. Provide friendly, conversational responses. Always use tools provided.",
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
