"""Simple chat client for continuous conversation with the AgentCore agent."""

import json
import os
import sys
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
    """Get an access token from Cognito."""
    resp = requests.post(
        _TOKEN_ENDPOINT,
        data={"grant_type": "client_credentials", "scope": "agent/invoke"},
        auth=(_CLIENT_ID, _CLIENT_SECRET),
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_message(prompt: str, session_id: str, actor_id: str, access_token: str) -> str:
    """Send a message to the agent and return the formatted response."""
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
                "actorId": actor_id,
            }
        ),
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.content.decode()}"

    # Parse JSON response and extract output.value from AgentCore standard format
    try:
        response_data = response.json()
        if isinstance(response_data, dict) and "output" in response_data:
            return response_data["output"]["value"]
        return response.content.decode()
    except json.JSONDecodeError:
        # If not JSON, return raw response
        return response.content.decode()


def main():
    """Run the interactive chat client."""
    print("Starting interactive chat with agent...")
    print("🤖 AgentCore Chat Client")
    print("Type 'exit' or 'quit' to end the conversation")
    print("-" * 50)

    # Initialise session
    session_id = str(uuid.uuid4())
    actor_id = os.environ.get("ACTOR_ID", f"user-{uuid.uuid4().hex[:8]}")
    access_token = _get_access_token()

    print(f"Session ID: {session_id}")
    print(f"Actor ID: {actor_id}\n")

    while True:
        try:
            # Get user input
            user_input = input("👤 You: ").strip()

            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break

            # Skip empty inputs
            if not user_input:
                continue

            # Send message and display response
            response = send_message(user_input, session_id, actor_id, access_token)
            print(f"\n🤖 Agent:\n{response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
            # Try to refresh token on auth errors
            if "401" in str(e) or "403" in str(e):
                print("Refreshing access token...")
                try:
                    access_token = _get_access_token()
                except Exception as token_error:
                    print(f"Failed to refresh token: {token_error}")
                    print("Exiting...")
                    sys.exit(1)


if __name__ == "__main__":
    main()
