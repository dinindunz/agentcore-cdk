import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import custom_resources as cr
from aws_cdk.aws_bedrock_agentcore_alpha import GatewayCredentialProvider
from constructs import Construct

from ..utils import to_kebab_case
from .cognito import UserPoolConstruct


class OAuth2CredentialProviderConstruct(Construct):
    """AgentCore OAuth2 credential provider backed by a Cognito user pool."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        provider_name: str,
        user_pool: UserPoolConstruct,
        scopes: list[str],
    ) -> None:
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)
        token_vault_base = f"arn:aws:bedrock-agentcore:{stack.region}:{stack.account}:token-vault/default"

        self._name = f"{stack_prefix}-{to_kebab_case(provider_name)}"

        provider = cr.AwsCustomResource(
            self,
            "Provider",
            install_latest_aws_sdk=True,
            on_create=cr.AwsSdkCall(
                service="@aws-sdk/client-bedrock-agentcore-control",
                action="CreateOauth2CredentialProvider",
                parameters={
                    "name": self._name,
                    "credentialProviderVendor": "CustomOauth2",
                    "oauth2ProviderConfigInput": {
                        "customOauth2ProviderConfig": {
                            "oauthDiscovery": {
                                "discoveryUrl": f"https://cognito-idp.{stack.region}.amazonaws.com/{user_pool.user_pool.user_pool_id}/.well-known/openid-configuration",
                            },
                            "clientId": user_pool.client.user_pool_client_id,
                            "clientSecret": user_pool.client.user_pool_client_secret.unsafe_unwrap(),
                        },
                    },
                },
                physical_resource_id=cr.PhysicalResourceId.from_response(
                    "credentialProviderArn"
                ),
            ),
            on_delete=cr.AwsSdkCall(
                service="@aws-sdk/client-bedrock-agentcore-control",
                action="DeleteOauth2CredentialProvider",
                parameters={"name": self._name},
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=[
                            "bedrock-agentcore:CreateTokenVault",
                            "bedrock-agentcore:GetTokenVault",
                            "bedrock-agentcore:CreateOauth2CredentialProvider",
                            "bedrock-agentcore:DeleteOauth2CredentialProvider",
                        ],
                        resources=[f"{token_vault_base}*"],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "secretsmanager:CreateSecret",
                            "secretsmanager:DeleteSecret",
                        ],
                        resources=[
                            f"arn:aws:secretsmanager:{stack.region}:{stack.account}:secret:bedrock-agentcore-identity!default/oauth2/{self._name}*",
                        ],
                    ),
                ]
            ),
        )

        provider_arn = provider.get_response_field("credentialProviderArn")
        secret_arn = provider.get_response_field("clientSecretArn.secretArn")

        self._credential_provider = GatewayCredentialProvider.from_oauth_identity_arn(
            provider_arn=provider_arn,
            secret_arn=secret_arn,
            scopes=scopes,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def credential_provider(self) -> GatewayCredentialProvider:
        return self._credential_provider


class ApiKeyCredentialProviderConstruct(Construct):
    """AgentCore API key credential provider."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        provider_name: str,
        api_key: str,
    ) -> None:
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)
        token_vault_base = f"arn:aws:bedrock-agentcore:{stack.region}:{stack.account}:token-vault/default"

        self._name = f"{stack_prefix}-{to_kebab_case(provider_name)}"

        provider = cr.AwsCustomResource(
            self,
            "Provider",
            install_latest_aws_sdk=True,
            on_create=cr.AwsSdkCall(
                service="@aws-sdk/client-bedrock-agentcore-control",
                action="CreateApiKeyCredentialProvider",
                parameters={
                    "name": self._name,
                    "apiKey": api_key,
                },
                physical_resource_id=cr.PhysicalResourceId.from_response(
                    "credentialProviderArn"
                ),
            ),
            on_delete=cr.AwsSdkCall(
                service="@aws-sdk/client-bedrock-agentcore-control",
                action="DeleteApiKeyCredentialProvider",
                parameters={"name": self._name},
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=[
                            "bedrock-agentcore:CreateTokenVault",
                            "bedrock-agentcore:GetTokenVault",
                            "bedrock-agentcore:CreateApiKeyCredentialProvider",
                            "bedrock-agentcore:DeleteApiKeyCredentialProvider",
                        ],
                        resources=[f"{token_vault_base}*"],
                    ),
                    iam.PolicyStatement(
                        actions=[
                            "secretsmanager:CreateSecret",
                            "secretsmanager:DeleteSecret",
                        ],
                        resources=[
                            f"arn:aws:secretsmanager:{stack.region}:{stack.account}:secret:bedrock-agentcore-identity!default/apikey/{self._name}*",
                        ],
                    ),
                ]
            ),
        )

        provider_arn = provider.get_response_field("credentialProviderArn")
        secret_arn = provider.get_response_field("apiKeySecretArn.secretArn")

        self._credential_provider = GatewayCredentialProvider.from_api_key_identity_arn(
            provider_arn=provider_arn,
            secret_arn=secret_arn,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def credential_provider(self) -> GatewayCredentialProvider:
        return self._credential_provider
