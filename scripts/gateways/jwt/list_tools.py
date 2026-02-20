import json
import os

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ["REGION_NAME"]

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
sm_client = boto3.client("secretsmanager", region_name=REGION_NAME)

GATEWAY_URL = ssm_client.get_parameter(Name="/agent-core-stack-dev/jwt-gateway-url")[
    "Parameter"
]["Value"]

# Fetch Cognito credentials from Secrets Manager
gateway_cognito = json.loads(
    sm_client.get_secret_value(SecretId="agent-core-stack-dev/gateway-cognito")[
        "SecretString"
    ]
)

# Get OAuth2 access token using client_credentials flow
token_response = requests.post(
    gateway_cognito["token_endpoint"],
    data={
        "grant_type": "client_credentials",
        "scope": "gateway/invoke",
    },
    auth=(gateway_cognito["client_id"], gateway_cognito["client_secret"]),
)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": f"Bearer {access_token}",
}

payload = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
)

print(f"JWT Gateway: {GATEWAY_URL}")

response = requests.post(GATEWAY_URL, headers=headers, data=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
