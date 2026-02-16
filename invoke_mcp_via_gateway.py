import hashlib
import json
import uuid

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

REGION_NAME = "ap-southeast-2"

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
GATEWAY_URL = ssm_client.get_parameter(Name="/agentcore/gateway-url")["Parameter"]["Value"]

session_id = str(uuid.uuid4())

# First, list available tools
list_tools_payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {},
})

# Then call the add tool (will use the correct name after listing)
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


def sigv4_sign(url, method, body, region, service):
    """Sign a request with SigV4 and return headers."""
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    aws_request = AWSRequest(
        method=method,
        url=url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-Amz-Content-Sha256": hashlib.sha256(body.encode()).hexdigest(),
        },
    )

    SigV4Auth(credentials, service, region).add_auth(aws_request)
    return dict(aws_request.headers)


# List tools first
print(f"Invoking Gateway at: {GATEWAY_URL}")
print("\n=== Listing tools ===")
headers = sigv4_sign(GATEWAY_URL, "POST", list_tools_payload, REGION_NAME, "bedrock-agentcore")
response = requests.post(GATEWAY_URL, headers=headers, data=list_tools_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content}")

# Call add tool
print("\n=== Calling add tool ===")
headers = sigv4_sign(GATEWAY_URL, "POST", call_tool_payload, REGION_NAME, "bedrock-agentcore")
response = requests.post(GATEWAY_URL, headers=headers, data=call_tool_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content}")
