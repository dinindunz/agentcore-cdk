import json
import uuid

import boto3
import requests

REGION_NAME = "ap-southeast-2"

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
GATEWAY_URL = ssm_client.get_parameter(Name="/agentcore/gateway-url")["Parameter"]["Value"]
TOKEN_ENDPOINT = ssm_client.get_parameter(Name="/agentcore/cognito-token-endpoint")["Parameter"]["Value"]
CLIENT_ID = ssm_client.get_parameter(Name="/agentcore/cognito-client-id")["Parameter"]["Value"]
CLIENT_SECRET = ssm_client.get_parameter(Name="/agentcore/cognito-client-secret")["Parameter"]["Value"]

# Get OAuth2 access token using client_credentials flow
token_response = requests.post(
    TOKEN_ENDPOINT,
    data={
        "grant_type": "client_credentials",
        "scope": "agentcore/invoke",
    },
    auth=(CLIENT_ID, CLIENT_SECRET),
)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": f"Bearer {access_token}",
}

session_id = str(uuid.uuid4())

# First, list available tools
list_tools_payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {},
})

# Then call the add tool
call_tool_payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "mcp-calculator___add",
        "arguments": {
            "a": 10,
            "b": 5,
        },
    },
})


# List tools first
print(f"Invoking Gateway at: {GATEWAY_URL}")
print("\n=== Listing tools ===")
response = requests.post(GATEWAY_URL, headers=headers, data=list_tools_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content}")

# Call add tool
print("\n=== Calling add tool ===")
response = requests.post(GATEWAY_URL, headers=headers, data=call_tool_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content}")
