import json
import os
import uuid

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

session_id = str(uuid.uuid4())

# Call celsius_to_fahrenheit: 100°C → 212°F
celsius_to_fahrenheit_payload = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "temperature-converter___celsius_to_fahrenheit",
            "arguments": {
                "celsius": 100,
            },
        },
    }
)

# Call fahrenheit_to_celsius: 32°F → 0°C
fahrenheit_to_celsius_payload = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "temperature-converter___fahrenheit_to_celsius",
            "arguments": {
                "fahrenheit": 32,
            },
        },
    }
)


print(f"Invoking JWT Gateway at: {GATEWAY_URL}")

print("\n=== Calling celsius_to_fahrenheit (100°C) ===")
response = requests.post(
    GATEWAY_URL, headers=headers, data=celsius_to_fahrenheit_payload
)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content}")

print("\n=== Calling fahrenheit_to_celsius (32°F) ===")
response = requests.post(
    GATEWAY_URL, headers=headers, data=fahrenheit_to_celsius_payload
)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.content}")
