import os

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import custom_resources as cr
from aws_cdk.aws_bedrock_agentcore_alpha import (
    ProtocolType,
    GatewayAuthorizer,
    GatewayCredentialProvider,
    ToolSchema,
)
from constructs import Construct

from .constructs import UserPoolConstruct, RuntimeConstruct, GatewayConstruct
from .utils import to_kebab_case


class AgentcoreCdkStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stack_prefix = to_kebab_case(self.stack_name)

        # ---------------------------------------------------------------
        # Cognito User Pools
        # ---------------------------------------------------------------

        # Agent Runtime User Pool — used for authentication to invoke the agent runtime.
        agent_auth = UserPoolConstruct(
            self,
            "AgentUserPool",
            name="agent",
            scope_description="Invoke agent runtime",
        )

        # Gateway User Pool — used for authentication to access the JWT gateway.
        gateway_auth = UserPoolConstruct(
            self,
            "JwtGatewayUserPool",
            name="gateway",
            scope_description="Invoke AgentCore Gateway",
        )

        # MCP Runtime User Pool — used for authentication to invoke the MCP runtime and as the identity source for the MCP OAuth2 credential provider.
        mcp_auth = UserPoolConstruct(
            self,
            "McpUserPool",
            name="mcp",
            scope_description="Invoke MCP runtimes",
        )

        # ---------------------------------------------------------------
        # AgentCore Identity - OAuth2 Credential Provider — Stores MCP Cognito credentials
        # ---------------------------------------------------------------
        mcp_oauth_provider_name = f"{stack_prefix}-mcp-runtime-oauth-provider"
        mcp_oauth_provider = cr.AwsCustomResource(
            self,
            "McpOAuthCredentialProvider",
            install_latest_aws_sdk=True,
            on_create=cr.AwsSdkCall(
                service="@aws-sdk/client-bedrock-agentcore-control",
                action="CreateOauth2CredentialProvider",
                parameters={
                    "name": mcp_oauth_provider_name,
                    "credentialProviderVendor": "CustomOauth2",
                    "oauth2ProviderConfigInput": {
                        "customOauth2ProviderConfig": {
                            "oauthDiscovery": {
                                "discoveryUrl": f"https://cognito-idp.{self.region}.amazonaws.com/{mcp_auth.user_pool.user_pool_id}/.well-known/openid-configuration",
                            },
                            "clientId": mcp_auth.client.user_pool_client_id,
                            "clientSecret": mcp_auth.client.user_pool_client_secret.unsafe_unwrap(),
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
                parameters={
                    "name": mcp_oauth_provider_name,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=[
                            "bedrock-agentcore:CreateTokenVault",
                            "bedrock-agentcore:GetTokenVault",
                            "bedrock-agentcore:CreateOauth2CredentialProvider",
                            "bedrock-agentcore:DeleteOauth2CredentialProvider",
                            "secretsmanager:CreateSecret",
                            "secretsmanager:DeleteSecret",
                        ],
                        resources=["*"],
                    ),
                ]
            ),
        )

        mcp_oauth_provider_arn = mcp_oauth_provider.get_response_field(
            "credentialProviderArn"
        )
        mcp_oauth_secret_arn = mcp_oauth_provider.get_response_field(
            "clientSecretArn.secretArn"
        )
        # Register the MCP OAuth2 credential provider with the CDK app so it can be referenced by the gateways when adding targets
        mcp_credential_provider = GatewayCredentialProvider.from_oauth_identity_arn(
            provider_arn=mcp_oauth_provider_arn,
            secret_arn=mcp_oauth_secret_arn,
            scopes=["mcp/invoke"],
        )

        # ---------------------------------------------------------------
        # Gateways — created before the agent runtime so their SSM paths
        # can be injected as environment variables into the agent container
        # ---------------------------------------------------------------

        # JWT Gateway — Cognito-authenticated MCP gateway
        jwt_gw = GatewayConstruct(
            self,
            "JwtGateway",
            gateway_name="jwt-gateway",
            authorizer_configuration=GatewayAuthorizer.using_cognito(
                user_pool=gateway_auth.user_pool,
                allowed_clients=[gateway_auth.client],
            ),
            credential_provider_name=mcp_oauth_provider_name,
        )

        # IAM Gateway — SigV4-authenticated MCP gateway
        iam_gw = GatewayConstruct(
            self,
            "IamGateway",
            gateway_name="iam-gateway",
            authorizer_configuration=GatewayAuthorizer.using_aws_iam(),
            credential_provider_name=mcp_oauth_provider_name,
        )

        # ---------------------------------------------------------------
        # AgentCore Runtimes
        # ---------------------------------------------------------------

        # Agent Runtime — the "agent" runtime that will orchestrate calls to the gateways and execute tools
        agent_rt = RuntimeConstruct(
            self,
            "AgentRuntime",
            runtime_name="agent",
            asset_path="agent",
            protocol=ProtocolType.HTTP,
            auth_pool=agent_auth,
            environment_variables={
                "JWT_GATEWAY_SSM_PATH": jwt_gw.ssm_url_param_name,
                "IAM_GATEWAY_SSM_PATH": iam_gw.ssm_url_param_name,
                "GATEWAY_COGNITO_SECRET": gateway_auth.secret_name,
            },
        )

        # Grant the agent runtime's execution role permission to invoke the IAM gateway
        # The JWT gateway uses Cognito auth — access is determined by token validity alone
        agent_rt.role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock-agentcore:InvokeGateway"],
                resources=[
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:gateway/{iam_gw.gateway.gateway_id}"
                ],
            )
        )

        # MCP Calculator Runtime — a simple MCP runtime that exposes calculator tools (add, subtract, multiply, divide) for demonstration purposes
        mcp_calculator_rt = RuntimeConstruct(
            self,
            "McpCalculatorRuntime",
            runtime_name="mcp_calculator",
            asset_path="mcp/calculator",
            protocol=ProtocolType.MCP,
            auth_pool=mcp_auth,
        )

        # URL-encode the runtime ARN for the MCP calculator invocation endpoint
        escaped_arn = cdk.Fn.join(
            "%2F",
            cdk.Fn.split(
                "/",
                cdk.Fn.join(
                    "%3A",
                    cdk.Fn.split(":", mcp_calculator_rt.runtime.agent_runtime_arn),
                ),
            ),
        )
        mcp_calculator_runtime_endpoint = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{escaped_arn}/invocations?qualifier=DEFAULT"

        # ---------------------------------------------------------------
        # MCP Lambdas
        # ---------------------------------------------------------------

        # Temperature Converter Lambda — a simple Lambda function that performs temperature conversions (Celsius <> Fahrenheit)
        temperature_lambda = lambda_.DockerImageFunction(
            self,
            "McpTemperatureConverter",
            function_name=f"{stack_prefix}-mcp-temperature-converter",
            architecture=lambda_.Architecture.ARM_64,
            code=lambda_.DockerImageCode.from_image_asset(
                os.path.join(
                    os.path.dirname(__file__), "..", "mcp", "temperature_converter"
                ),
                platform=ecr_assets.Platform.LINUX_ARM64,
            ),
        )

        # ---------------------------------------------------------------
        # Gateway Targets
        # ---------------------------------------------------------------

        # MCP Calculator Runtime Target to IAM Gateway
        iam_gw.gateway.add_mcp_server_target(
            "CalculatorTarget",
            gateway_target_name="calculator",
            description="Calculator tools (add, subtract, multiply, divide)",
            endpoint=mcp_calculator_runtime_endpoint,
            credential_provider_configurations=[mcp_credential_provider],
        )

        # Temperature Converter Lambda Target to JWT Gateway
        jwt_gw.gateway.add_lambda_target(
            "TemperatureConverterTarget",
            gateway_target_name="temperature-converter",
            description="Temperature conversion tools (Celsius <> Fahrenheit)",
            lambda_function=temperature_lambda,
            tool_schema=ToolSchema.from_local_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "mcp",
                    "temperature_converter",
                    "schema.json",
                )
            ),
        )

        # ---------------------------------------------------------------
        # Stack Outputs
        # ---------------------------------------------------------------
        cdk.CfnOutput(
            self,
            "IamGatewayUrl",
            value=f"https://{iam_gw.gateway.gateway_id}.gateway.bedrock-agentcore.{self.region}.amazonaws.com/mcp",
        )
        cdk.CfnOutput(
            self,
            "JwtGatewayUrl",
            value=f"https://{jwt_gw.gateway.gateway_id}.gateway.bedrock-agentcore.{self.region}.amazonaws.com/mcp",
        )
        cdk.CfnOutput(
            self, "JwtGatewayUserPoolId", value=gateway_auth.user_pool.user_pool_id
        )
        cdk.CfnOutput(
            self,
            "JwtGatewayUserPoolClientId",
            value=gateway_auth.client.user_pool_client_id,
        )
        cdk.CfnOutput(
            self,
            "JwtGatewayTokenEndpoint",
            value=f"{gateway_auth.domain.base_url()}/oauth2/token",
        )
        cdk.CfnOutput(self, "AgentUserPoolId", value=agent_auth.user_pool.user_pool_id)
        cdk.CfnOutput(
            self, "AgentUserPoolClientId", value=agent_auth.client.user_pool_client_id
        )
        cdk.CfnOutput(
            self,
            "AgentTokenEndpoint",
            value=f"{agent_auth.domain.base_url()}/oauth2/token",
        )
        cdk.CfnOutput(self, "McpUserPoolId", value=mcp_auth.user_pool.user_pool_id)
        cdk.CfnOutput(
            self, "McpUserPoolClientId", value=mcp_auth.client.user_pool_client_id
        )
        cdk.CfnOutput(
            self, "McpTokenEndpoint", value=f"{mcp_auth.domain.base_url()}/oauth2/token"
        )
        cdk.CfnOutput(self, "AgentRuntimeArn", value=agent_rt.runtime.agent_runtime_arn)
        cdk.CfnOutput(
            self,
            "McpCalculatorRuntimeArn",
            value=mcp_calculator_rt.runtime.agent_runtime_arn,
        )
        cdk.CfnOutput(self, "McpOAuthProviderArn", value=mcp_oauth_provider_arn)
        cdk.CfnOutput(self, "McpOAuthSecretArn", value=mcp_oauth_secret_arn)
