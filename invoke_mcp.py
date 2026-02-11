import base64
import json
import urllib.parse
import uuid

import boto3
import requests

# === Fetch config from SSM ===
REGION_NAME = "ap-southeast-2"
ssm_client = boto3.client("ssm", region_name=REGION_NAME)


def get_ssm_param(name):
    return ssm_client.get_parameter(Name=name)["Parameter"]["Value"]


CLIENT_ID = get_ssm_param("/agentcore/cognito-client-id")
TOKEN_ENDPOINT = get_ssm_param("/agentcore/cognito-token-endpoint")
USER_POOL_ID = get_ssm_param("/agentcore/cognito-user-pool-id")
mcp_calculator_arn = get_ssm_param("/agentcore/mcp-calculator-runtime-arn")

# Fetch client secret from Cognito
cognito_client = boto3.client("cognito-idp", region_name=REGION_NAME)
CLIENT_SECRET = cognito_client.describe_user_pool_client(
    UserPoolId=USER_POOL_ID,
    ClientId=CLIENT_ID,
)["UserPoolClient"]["ClientSecret"]

session_id = str(uuid.uuid4())

# === Authenticate with Cognito (client credentials) ===
token_response = requests.post(
    TOKEN_ENDPOINT,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(),
    },
    data={
        "grant_type": "client_credentials",
        "scope": "agentcore/invoke",
    },
)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]
print("Cognito authentication successful")

# === Invoke MCP Calculator ===
escaped_arn = urllib.parse.quote(mcp_calculator_arn, safe="")
url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_arn}/invocations?qualifier=DEFAULT"
print(f"Invoking MCP Calculator at URL: {url}")

# MCP JSON-RPC 2.0 payload to call the "add" tool
payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "add",
        "arguments": {
            "a": 10,
            "b": 5,
        },
    },
})

invoke_response = requests.post(
    url,
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {access_token}",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
    },
    data=payload,
)

print(f"Status Code: {invoke_response.status_code}")
print(f"Response: {invoke_response.content}")
