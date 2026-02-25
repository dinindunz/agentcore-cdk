"""Configuration management for the agent runtime.

This module provides centralised configuration management with lazy loading
from environment variables and AWS services (SSM Parameter Store, Secrets Manager)
to eliminate module-level side effects and improve testability.
"""

import json
import os
from functools import lru_cache
from typing import TypedDict

import boto3

from common.logger import logger


class GatewayCognitoConfig(TypedDict):
    """Cognito configuration for gateway authentication.

    Attributes:
        token_endpoint: OAuth2 token endpoint URL
        client_id: Cognito app client ID
        client_secret: Cognito app client secret
    """

    token_endpoint: str
    client_id: str
    client_secret: str


class AgentConfig:
    """Central configuration for the agent runtime.

    Loads configuration from environment variables and AWS services
    (SSM Parameter Store, Secrets Manager) on-demand using lazy properties.
    This eliminates module-level side effects and makes configuration testable.

    Attributes:
        region_name: AWS region name (from REGION_NAME env var)
        skills_bucket: S3 bucket name for skills (from SKILLS_BUCKET env var, optional)
        memory_id: AgentCore Memory ID (from MEMORY_ID env var, optional)
    """

    def __init__(self) -> None:
        """Initialise configuration with required environment variables."""
        self.region_name: str = os.environ["REGION_NAME"]
        self.skills_bucket: str | None = os.environ.get("SKILLS_BUCKET")
        self.memory_id: str | None = os.environ.get("MEMORY_ID")

        logger.debug(
            f"[Config] Initialised: region={self.region_name} "
            f"skills_bucket={self.skills_bucket or 'None'} "
            f"memory_id={self.memory_id or 'None'}"
        )

        # Private cached properties (lazy-loaded)
        self._jwt_gateway_url: str | None = None
        self._iam_gateway_url: str | None = None
        self._gateway_cognito: GatewayCognitoConfig | None = None

        # Boto3 clients (created lazily)
        self._ssm_client: boto3.client | None = None
        self._sm_client: boto3.client | None = None
        self._s3_client: boto3.client | None = None

    @property
    def ssm_client(self) -> boto3.client:
        """Lazy-load SSM client."""
        if self._ssm_client is None:
            logger.debug(f"[Config] Creating SSM client: region={self.region_name}")
            self._ssm_client = boto3.client("ssm", region_name=self.region_name)
        return self._ssm_client

    @property
    def sm_client(self) -> boto3.client:
        """Lazy-load Secrets Manager client."""
        if self._sm_client is None:
            logger.debug(f"[Config] Creating Secrets Manager client: region={self.region_name}")
            self._sm_client = boto3.client("secretsmanager", region_name=self.region_name)
        return self._sm_client

    @property
    def s3_client(self) -> boto3.client:
        """Lazy-load S3 client."""
        if self._s3_client is None:
            logger.debug(f"[Config] Creating S3 client: region={self.region_name}")
            self._s3_client = boto3.client("s3", region_name=self.region_name)
        return self._s3_client

    @property
    def jwt_gateway_url(self) -> str:
        """
        Lazy-load JWT gateway URL from SSM Parameter Store.

        Returns:
            JWT gateway invocation URL

        Raises:
            KeyError: If JWT_GATEWAY_SSM_PATH environment variable is not set
            botocore.exceptions.ClientError: If SSM parameter cannot be retrieved
        """
        if self._jwt_gateway_url is None:
            param_name = os.environ["JWT_GATEWAY_SSM_PATH"]
            logger.debug(f"[Config] Loading JWT gateway URL from SSM: param={param_name}")
            response = self.ssm_client.get_parameter(Name=param_name)
            self._jwt_gateway_url = response["Parameter"]["Value"]
            logger.debug(f"[Config] JWT gateway URL loaded: url={self._jwt_gateway_url}")
        return self._jwt_gateway_url

    @property
    def iam_gateway_url(self) -> str:
        """
        Lazy-load IAM gateway URL from SSM Parameter Store.

        Returns:
            IAM gateway invocation URL

        Raises:
            KeyError: If IAM_GATEWAY_SSM_PATH environment variable is not set
            botocore.exceptions.ClientError: If SSM parameter cannot be retrieved
        """
        if self._iam_gateway_url is None:
            param_name = os.environ["IAM_GATEWAY_SSM_PATH"]
            logger.debug(f"[Config] Loading IAM gateway URL from SSM: param={param_name}")
            response = self.ssm_client.get_parameter(Name=param_name)
            self._iam_gateway_url = response["Parameter"]["Value"]
            logger.debug(f"[Config] IAM gateway URL loaded: url={self._iam_gateway_url}")
        return self._iam_gateway_url

    @property
    def gateway_cognito(self) -> GatewayCognitoConfig:
        """
        Lazy-load Cognito configuration from Secrets Manager.

        Returns:
            Cognito configuration dictionary with token_endpoint, client_id,
            and client_secret

        Raises:
            KeyError: If GATEWAY_COGNITO_SECRET environment variable is not set
            botocore.exceptions.ClientError: If secret cannot be retrieved
            json.JSONDecodeError: If secret value is not valid JSON
        """
        if self._gateway_cognito is None:
            secret_name = os.environ["GATEWAY_COGNITO_SECRET"]
            logger.debug(
                f"[Config] Loading Cognito config from Secrets Manager: secret={secret_name}"
            )
            response = self.sm_client.get_secret_value(SecretId=secret_name)
            self._gateway_cognito = json.loads(response["SecretString"])
            logger.debug(
                f"[Config] Cognito config loaded: "
                f"endpoint={self._gateway_cognito['token_endpoint']} "
                f"client_id={self._gateway_cognito['client_id']}"
            )
        return self._gateway_cognito


@lru_cache
def get_config() -> AgentConfig:
    """
    Get singleton configuration instance.

    Uses lru_cache to ensure only one AgentConfig instance is created
    throughout the application lifecycle.

    Returns:
        Singleton AgentConfig instance
    """
    logger.debug("[Config] Creating singleton AgentConfig instance")
    return AgentConfig()
