import json
import os
import sys
import urllib.request
import urllib.error

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ["REGION_NAME"]
SERVICE_NAME = "bedrock-agentcore"

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
GATEWAY_URL = ssm_client.get_parameter(Name="/agent-core-stack-dev/iam-gateway-url")[
    "Parameter"
]["Value"]

session = boto3.Session(region_name=REGION_NAME)
credentials = session.get_credentials().get_frozen_credentials()

headers = {
    "Content-Type": "application/json",
}

query = sys.argv[1] if len(sys.argv) > 1 else "add two numbers"

payload = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": "search-tools-request",
        "method": "tools/call",
        "params": {
            "name": "x_amz_bedrock_agentcore_search",
            "arguments": {
                "query": query,
            },
        },
    }
)

request = AWSRequest(method="POST", url=GATEWAY_URL, data=payload, headers=headers)
SigV4Auth(credentials, SERVICE_NAME, REGION_NAME).add_auth(request)

req = urllib.request.Request(
    GATEWAY_URL,
    data=payload.encode("utf-8"),
    headers=dict(request.headers),
    method="POST",
)

print(f"Searching IAM Gateway at: {GATEWAY_URL}")
print(f"Query: {query}\n")

try:
    with urllib.request.urlopen(req) as resp:
        print(json.dumps(json.loads(resp.read()), indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read()}")
