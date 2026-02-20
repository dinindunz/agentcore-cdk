import base64
import json
import os
import urllib.parse
import uuid

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

# === Fetch config from AWS ===
REGION_NAME = os.environ["REGION_NAME"]
ssm_client = boto3.client("ssm", region_name=REGION_NAME)
secrets_client = boto3.client("secretsmanager", region_name=REGION_NAME)


def get_ssm_param(name):
    return ssm_client.get_parameter(Name=name)["Parameter"]["Value"]


def get_secret(name):
    response = secrets_client.get_secret_value(SecretId=name)
    return json.loads(response["SecretString"])


# Fetch MCP Cognito credentials from Secrets Manager
mcp_cognito = get_secret("agent-core-stack-dev/mcp-cognito")
CLIENT_ID = mcp_cognito["client_id"]
CLIENT_SECRET = mcp_cognito["client_secret"]
TOKEN_ENDPOINT = mcp_cognito["token_endpoint"]
USER_POOL_ID = mcp_cognito["user_pool_id"]

# Fetch MCP Calculator runtime ARN from SSM
mcp_calculator_arn = get_ssm_param("/agent-core-stack-dev/mcp-calculator-runtime-arn")

session_id = str(uuid.uuid4())

# === Authenticate with Cognito (client credentials) ===
token_response = requests.post(
    TOKEN_ENDPOINT,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic "
        + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(),
    },
    data={
        "grant_type": "client_credentials",
        "scope": "mcp/invoke",
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
payload = json.dumps(
    {
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
    }
)

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
