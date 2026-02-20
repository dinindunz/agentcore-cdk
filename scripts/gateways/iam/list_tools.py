import json
import os

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
    "Accept": "application/json, text/event-stream",
}

payload = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
)

print(f"IAM Gateway: {GATEWAY_URL}")

request = AWSRequest(method="POST", url=GATEWAY_URL, data=payload, headers=headers)
SigV4Auth(credentials, SERVICE_NAME, REGION_NAME).add_auth(request)

import urllib.request

req = urllib.request.Request(
    GATEWAY_URL,
    data=payload.encode("utf-8"),
    headers=dict(request.headers),
    method="POST",
)
try:
    with urllib.request.urlopen(req) as resp:
        print(f"Status Code: {resp.status}")
        print(f"Response: {json.dumps(json.loads(resp.read()), indent=2)}")
except urllib.error.HTTPError as e:
    print(f"Status Code: {e.code}")
    print(f"Response: {e.read().decode()}")
