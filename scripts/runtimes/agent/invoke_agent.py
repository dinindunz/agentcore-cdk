import json
import os
import urllib.parse
import uuid

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ["REGION_NAME"]
_ssm = boto3.client("ssm", region_name=REGION_NAME)
_sm = boto3.client("secretsmanager", region_name=REGION_NAME)

# Fetch Cognito credentials from Secrets Manager
_agent_cognito = json.loads(
    _sm.get_secret_value(SecretId="agent-core-stack-dev/agent-cognito")["SecretString"]
)
_CLIENT_ID = _agent_cognito["client_id"]
_CLIENT_SECRET = _agent_cognito["client_secret"]
_TOKEN_ENDPOINT = _agent_cognito["token_endpoint"]

_agent_arn = _ssm.get_parameter(Name="/agent-core-stack-dev/agent-runtime-arn")["Parameter"][
    "Value"
]

_escaped_arn = urllib.parse.quote(_agent_arn, safe="")
_URL = f"https://bedrock-agentcore.{REGION_NAME}.amazonaws.com/runtimes/{_escaped_arn}/invocations?qualifier=DEFAULT"


def _get_access_token() -> str:
    resp = requests.post(
        _TOKEN_ENDPOINT,
        data={"grant_type": "client_credentials", "scope": "agent/invoke"},
        auth=(_CLIENT_ID, _CLIENT_SECRET),
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def invoke_agent(prompt: str) -> None:
    """Authenticate and invoke the agent with the given prompt, printing the response."""
    access_token = _get_access_token()
    session_id = str(uuid.uuid4())
    actor_id = os.environ.get("ACTOR_ID", f"user-{uuid.uuid4().hex[:8]}")

    print(f"Prompt: {prompt}")
    print(f"Session ID: {session_id}")
    print(f"Actor ID: {actor_id}\n")

    response = requests.post(
        _URL,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {access_token}",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
        },
        data=json.dumps(
            {
                "prompt": prompt,
                "session_id": session_id,
                "actor_id": actor_id,
            }
        ),
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")
