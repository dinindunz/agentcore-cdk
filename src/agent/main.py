import hashlib
import json
import os
import boto3
import botocore.auth
import botocore.awsrequest
import httpx
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient


REGION_NAME = os.environ["REGION_NAME"]
SKILLS_BUCKET = os.environ.get("SKILLS_BUCKET")

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
sm_client = boto3.client("secretsmanager", region_name=REGION_NAME)
s3_client = boto3.client("s3", region_name=REGION_NAME)

JWT_GATEWAY_URL = ssm_client.get_parameter(Name=os.environ["JWT_GATEWAY_SSM_PATH"])[
    "Parameter"
]["Value"]
IAM_GATEWAY_URL = ssm_client.get_parameter(Name=os.environ["IAM_GATEWAY_SSM_PATH"])[
    "Parameter"
]["Value"]

# Fetch Cognito credentials from Secrets Manager
gateway_cognito = json.loads(
    sm_client.get_secret_value(SecretId=os.environ["GATEWAY_COGNITO_SECRET"])[
        "SecretString"
    ]
)


def get_access_token() -> str:
    """Get an OAuth2 access token using client_credentials flow."""
    response = httpx.post(
        gateway_cognito["token_endpoint"],
        data={
            "grant_type": "client_credentials",
            "scope": "gateway/invoke",
        },
        auth=(gateway_cognito["client_id"], gateway_cognito["client_secret"]),
    )
    response.raise_for_status()
    return response.json()["access_token"]


class SigV4Auth(httpx.Auth):
    """Signs requests with AWS SigV4 using the runtime's execution role credentials."""

    requires_request_body = True

    def __init__(self, region: str, service: str = "bedrock-agentcore"):
        self.region = region
        self.service = service
        self._boto_session = boto3.Session(region_name=region)

    def auth_flow(self, request: httpx.Request):
        # Refresh credentials each call to handle credential rotation on long-running containers
        credentials = self._boto_session.get_credentials().get_frozen_credentials()
        body = request.content or b""

        # Only sign Host + Content-Type to keep SignedHeaders minimal and stable
        aws_request = botocore.awsrequest.AWSRequest(
            method=request.method,
            url=str(request.url),
            data=body,
            headers={
                "Host": request.url.host,
                "Content-Type": request.headers.get("content-type", "application/json"),
            },
        )
        aws_request.headers["X-Amz-Content-Sha256"] = hashlib.sha256(body).hexdigest()

        signer = botocore.auth.SigV4Auth(credentials, self.service, self.region)
        signer.add_auth(aws_request)

        for key, value in aws_request.headers.items():
            request.headers[key] = value
        yield request


sigv4_auth = SigV4Auth(region=REGION_NAME)

app = BedrockAgentCoreApp()


def create_jwt_transport():
    # Fetch a fresh token on each connection to handle expiry in long-running containers
    token = get_access_token()
    return streamablehttp_client(
        JWT_GATEWAY_URL,
        headers={"Authorization": f"Bearer {token}"},
    )


def create_iam_transport():
    return streamablehttp_client(
        IAM_GATEWAY_URL,
        auth=sigv4_auth,
    )


def load_skills_summary() -> str:
    """Load skill markdown files from S3 and build a summary for the system prompt."""
    if not SKILLS_BUCKET:
        return ""
    resp = s3_client.list_objects_v2(Bucket=SKILLS_BUCKET)
    lines = []
    for obj in resp.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".md"):
            continue
        body = (
            s3_client.get_object(Bucket=SKILLS_BUCKET, Key=key)["Body"].read().decode()
        )
        # Extract title (first H1) and description (first non-empty line after title)
        title = ""
        description = ""
        for line in body.strip().split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not title:
                title = stripped[2:].strip()
            elif title and stripped and not stripped.startswith("#"):
                description = stripped
                break
        if title:
            lines.append(f"- **{title}**: {description}")

    if not lines:
        return ""
    return (
        "\n\n## Available Skills\n"
        "When a user's request matches a skill, use the search_skills tool to retrieve "
        "the full step-by-step instructions, then follow them.\n\n" + "\n".join(lines)
    )


jwt_client = MCPClient(lambda: create_jwt_transport())
jwt_client.__enter__()

iam_client = MCPClient(lambda: create_iam_transport())
iam_client.__enter__()

# TODO: Both gateways expose the tool search tool `x_amz_bedrock_agentcore_search` under the same name,
# so only the first one encountered (JWT) is loaded — the IAM gateway's search tool is silently dropped.
_seen_tool_names: set[str] = set()
tools = []
for tool in jwt_client.list_tools_sync() + iam_client.list_tools_sync():
    if tool.tool_name not in _seen_tool_names:
        _seen_tool_names.add(tool.tool_name)
        tools.append(tool)

skills_section = load_skills_summary()
agent = Agent(
    tools=tools,
    system_prompt=(
        "You are a helpful assistant. Provide friendly, conversational responses. "
        "Always use tools provided." + skills_section
    ),
)


@app.entrypoint
def invoke(payload):
    """Process user input and return a response"""
    user_message = payload.get("prompt", "Hello")
    result = agent(user_message)
    text = "".join(
        block["text"] for block in result.message.get("content", []) if "text" in block
    )
    return {"result": text}


app.run()
