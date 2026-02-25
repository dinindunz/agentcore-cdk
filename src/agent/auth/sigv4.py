"""AWS SigV4 authentication for httpx requests.

This module provides an httpx.Auth implementation that signs requests using
AWS Signature Version 4 (SigV4) for authenticating with IAM-protected
AgentCore gateways.
"""

import hashlib

import boto3
import botocore.auth
import botocore.awsrequest
import httpx

from common.logger import logger


class SigV4Auth(httpx.Auth):
    """
    Signs requests with AWS SigV4 using the runtime's execution role credentials.

    Credentials are refreshed on each request to handle rotation in long-running
    containers. The implementation uses boto3's credential chain to automatically
    discover credentials from the environment (IAM role, environment variables, etc.).

    Only the Host and Content-Type headers are included in the signature to keep
    the SignedHeaders list minimal and stable.

    Attributes:
        requires_request_body: Always True for SigV4 (body needed for signature)

    Example:
        # Create auth instance for AgentCore service
        auth = SigV4Auth(region="ap-southeast-2", service="bedrock-agentcore")

        # Use with httpx client
        with httpx.Client(auth=auth) as client:
            response = client.post(
                "https://bedrock-agentcore.ap-southeast-2.amazonaws.com/...",
                json={"key": "value"}
            )

        # Or with individual requests
        response = httpx.post(gateway_url, json=data, auth=auth)
    """

    requires_request_body = True

    def __init__(self, region: str, service: str = "bedrock-agentcore") -> None:
        """
        Initialise SigV4 authentication.

        Args:
            region: AWS region (e.g., "ap-southeast-2", "us-east-1")
            service: AWS service name for signature (default: "bedrock-agentcore")
        """
        self.region = region
        self.service = service
        self._boto_session = boto3.Session(region_name=region)
        logger.debug(f"[Auth] SigV4Auth initialised: region={region} service={service}")

    def auth_flow(self, request: httpx.Request):
        """
        Sign the request with AWS SigV4.

        This method is called automatically by httpx for each request when
        using this auth class.

        Args:
            request: The httpx request to sign

        Yields:
            The signed request with Authorization and other AWS headers added

        Note:
            Credentials are refreshed on each call to handle rotation in
            long-running containers.
        """
        logger.debug(f"[Auth] Signing request: method={request.method} url={request.url}")

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

        # Copy signed headers to the httpx request
        for key, value in aws_request.headers.items():
            request.headers[key] = value

        logger.debug(f"[Auth] Request signed: access_key={credentials.access_key[:8]}...")
        yield request
