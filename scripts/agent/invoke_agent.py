import json
import urllib.parse
import uuid

import boto3
import requests

REGION_NAME = "ap-southeast-2"
ssm_client = boto3.client("ssm", region_name=REGION_NAME)
sm_client = boto3.client("secretsmanager", region_name=REGION_NAME)

# Fetch Cognito credentials from Secrets Manager
agent_cognito = json.loads(
    sm_client.get_secret_value(SecretId="agentcore-cdk-stack-dev/agent-cognito")[
        "SecretString"
    ]
)
CLIENT_ID = agent_cognito["client_id"]
CLIENT_SECRET = agent_cognito["client_secret"]
TOKEN_ENDPOINT = agent_cognito["token_endpoint"]

agent_arn = ssm_client.get_parameter(Name="/agentcore-cdk-stack-dev/agent-runtime-arn")[
    "Parameter"
]["Value"]

session_id = str(uuid.uuid4())

# === Authenticate with Cognito (client credentials) ===
token_response = requests.post(
    TOKEN_ENDPOINT,
    data={
        "grant_type": "client_credentials",
        "scope": "agent/invoke",
    },
    auth=(CLIENT_ID, CLIENT_SECRET),
)
token_response.raise_for_status()
access_token = token_response.json()["access_token"]
print("Cognito authentication successful")

# === Invoke Agent with NL prompt ===
escaped_agent_arn = urllib.parse.quote(agent_arn, safe="")
url = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"
print(f"Invoking Agent at URL: {url}")

payload = json.dumps(
    {
        "prompt": "What is 2 + 5? And treat the output as celsius and convert it to fahrenheit.",
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
