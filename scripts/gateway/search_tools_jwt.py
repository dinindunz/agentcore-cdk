import json
import sys

import boto3
import requests

REGION_NAME = "ap-southeast-2"

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
sm_client = boto3.client("secretsmanager", region_name=REGION_NAME)

GATEWAY_URL = ssm_client.get_parameter(Name="/agentcore-cdk-stack-dev/jwt-gateway-url")[
    "Parameter"
]["Value"]

# Fetch Cognito credentials from Secrets Manager
gateway_cognito = json.loads(
    sm_client.get_secret_value(SecretId="agentcore-cdk-stack-dev/gateway-cognito")[
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
    "Authorization": f"Bearer {access_token}",
}

query = sys.argv[1] if len(sys.argv) > 1 else "convert Celsius to Fahrenheit"

payload = {
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

print(f"Searching JWT Gateway at: {GATEWAY_URL}")
print(f"Query: {query}\n")

response = requests.post(GATEWAY_URL, headers=headers, json=payload)
print(json.dumps(response.json(), indent=2))
