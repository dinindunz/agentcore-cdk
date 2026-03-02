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
_cognito = boto3.client("cognito-idp", region_name=REGION_NAME)

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


def _validate_and_lookup_actor(preferred_username: str) -> str:
    """
    Validate actor exists in Cognito and return their Cognito username.

    Looks up the user by preferred_username, validates they exist,
    and returns their Cognito username (UUID) for use as actor_id.

    Args:
        preferred_username: User's preferred_username from .env (e.g., "actor-123")

    Returns:
        Cognito username (UUID) that's valid for AgentCore Memory

    Exits:
        Exits with code 1 if user not found or validation fails
    """
    try:
        user_pool_id = _agent_cognito["user_pool_id"]

        # Look up user by preferred_username
        response = _cognito.list_users(
            UserPoolId=user_pool_id,
            Filter=f'preferred_username = "{preferred_username}"',
            Limit=1,
        )

        if response.get("Users"):
            username = response["Users"][0]["Username"]
            print(f"✓ Validated user '{preferred_username}' → Cognito username '{username}'")
            return username
        else:
            print(f"\n❌ Error: User '{preferred_username}' not found in Cognito User Pool")
            print(f"   Create user with: python scripts/create_user.py {preferred_username}")
            print("   Aborting invocation.\n")
            exit(1)

    except Exception as e:
        print(f"\n❌ Error: Could not validate actor: {e}")
        print("   Aborting invocation.\n")
        exit(1)


def invoke_agent(prompt: str) -> None:
    """Validate user authorization and invoke the agent with the given prompt."""
    session_id = str(uuid.uuid4())
    actor_id = os.environ.get("ACTOR_ID", f"user-{uuid.uuid4().hex[:8]}")

    # Validate user first (exits if not found)
    validated_actor_id = _validate_and_lookup_actor(actor_id)

    # Only get token if user is authorised
    access_token = _get_access_token()

    print(f"Prompt: {prompt}")
    print(f"Session ID: {session_id}")
    print(f"Actor ID: {validated_actor_id}\n")

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
                "input": {"value": prompt},
                "sessionId": session_id,
                "actorId": validated_actor_id,  # Send the validated Cognito username (UUID)
            }
        ),
    )

    print(f"Status: {response.status_code}")

    # Parse and display the response
    if response.status_code == 200:
        try:
            response_data = response.json()
            if "output" in response_data and "value" in response_data["output"]:
                print(f"Response: {response_data['output']['value']}")
            else:
                print(f"Response: {response.content.decode()}")
        except json.JSONDecodeError:
            print(f"Response: {response.content.decode()}")
    else:
        print(f"Response: {response.content.decode()}")
