import json
import uuid

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

REGION_NAME = "ap-southeast-2"
SERVICE_NAME = "bedrock-agentcore"

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
GATEWAY_URL = ssm_client.get_parameter(Name="/agentcore/iam-gateway-url")["Parameter"][
    "Value"
]

print(f"Gateway URL: {GATEWAY_URL}")

session = boto3.Session(region_name=REGION_NAME)
credentials = session.get_credentials().get_frozen_credentials()

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

session_id = str(uuid.uuid4())


def sigv4_request(url, data):
    """Send a SigV4-signed POST request."""
    request = AWSRequest(method="POST", url=url, data=data, headers=headers)
    SigV4Auth(credentials, SERVICE_NAME, REGION_NAME).add_auth(request)
    # Use urllib to send the signed request
    import urllib.request

    req = urllib.request.Request(
        url,
        data=data.encode("utf-8"),
        headers=dict(request.headers),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# List available tools
list_tools_payload = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
)

# Call the add tool
call_tool_payload = json.dumps(
    {
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
    }
)

print(f"\nInvoking IAM Gateway at: {GATEWAY_URL}")

print("\n=== Listing tools ===")
status, body = sigv4_request(GATEWAY_URL, list_tools_payload)
print(f"Status Code: {status}")
print(f"Response: {body}")

print("\n=== Calling add tool ===")
status, body = sigv4_request(GATEWAY_URL, call_tool_payload)
print(f"Status Code: {status}")
print(f"Response: {body}")
