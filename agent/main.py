import hashlib
from typing import Generator

import boto3
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

REGION_NAME = "ap-southeast-2"

ssm_client = boto3.client("ssm", region_name=REGION_NAME)
GATEWAY_URL = ssm_client.get_parameter(Name="/agentcore/gateway-url")["Parameter"]["Value"]


class HTTPXSigV4Auth(httpx.Auth):
    """httpx Auth handler that signs requests with AWS SigV4."""

    def __init__(self, service: str, region: str):
        session = boto3.Session()
        self.credentials = session.get_credentials().get_frozen_credentials()
        self.service = service
        self.region = region

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        # Read the body
        body = request.content if request.content else b""
        if isinstance(body, str):
            body = body.encode("utf-8")

        # Build an AWSRequest to sign
        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=body,
            headers={
                "Host": request.url.host,
                "Content-Type": request.headers.get("Content-Type", "application/json"),
            },
        )
        aws_request.headers["X-Amz-Content-Sha256"] = hashlib.sha256(body).hexdigest()

        # Sign the request
        signer = SigV4Auth(self.credentials, self.service, self.region)
        signer.add_auth(aws_request)

        # Copy signed headers back to the httpx request
        for key, value in aws_request.headers.items():
            request.headers[key] = value

        yield request


sigv4_auth = HTTPXSigV4Auth(service="bedrock-agentcore", region=REGION_NAME)

app = BedrockAgentCoreApp()


def create_mcp_transport():
    return streamablehttp_client(
        GATEWAY_URL,
        auth=sigv4_auth,
    )


mcp_client = MCPClient(lambda: create_mcp_transport())
mcp_client.__enter__()

tools = mcp_client.list_tools_sync()
agent = Agent(
    tools=tools,
    system_prompt="You are a helpful assistant. Provide friendly, conversational responses.",
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
