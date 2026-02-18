import os
import aws_cdk as cdk
from typing import NamedTuple
from aws_cdk import aws_iam as iam
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_ssm as ssm
from aws_cdk import custom_resources as cr
from aws_cdk.aws_bedrock_agentcore_alpha import (
    AgentRuntimeArtifact,
    Runtime,
    RuntimeAuthorizerConfiguration,
    ProtocolType,
    Gateway,
    GatewayAuthorizer,
    GatewayCredentialProvider,
    ToolSchema,
)
from constructs import Construct


class UserPoolResources(NamedTuple):
    user_pool: cognito.UserPool
    domain: cognito.UserPoolDomain
    resource_server: cognito.UserPoolResourceServer
    client: cognito.UserPoolClient


class RuntimeResources(NamedTuple):
    runtime: Runtime
    role: iam.Role


class AgentcoreCdkStack(cdk.Stack):

    def _create_user_pool(
        self,
        prefix: str,
        pool_name: str,
        domain_prefix: str,
        resource_server_id: str,
        scope_description: str,
        secret_name: str,
    ) -> UserPoolResources:
        """Create a Cognito user pool with domain, resource server, client, and credentials secret."""
        scope = cognito.ResourceServerScope(
            scope_name="invoke", scope_description=scope_description
        )

        user_pool = cognito.UserPool(
            self,
            f"{prefix}UserPool",
            user_pool_name=pool_name,
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        domain = user_pool.add_domain(
            f"{prefix}UserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix),
        )

        resource_server = user_pool.add_resource_server(
            f"{prefix}ResourceServer",
            identifier=resource_server_id,
            scopes=[scope],
        )

        client = user_pool.add_client(
            f"{prefix}UserPoolClient",
            generate_secret=True,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(client_credentials=True),
                scopes=[cognito.OAuthScope.resource_server(resource_server, scope)],
            ),
        )

        # Store all Cognito credentials in a single secret
        secretsmanager.Secret(
            self,
            f"{prefix}CognitoSecret",
            secret_name=secret_name,
            secret_object_value={
                "client_id": cdk.SecretValue.unsafe_plain_text(
                    client.user_pool_client_id
                ),
                "client_secret": client.user_pool_client_secret,
                "user_pool_id": cdk.SecretValue.unsafe_plain_text(
                    user_pool.user_pool_id
                ),
                "token_endpoint": cdk.SecretValue.unsafe_plain_text(
                    f"{domain.base_url()}/oauth2/token"
                ),
            },
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        return UserPoolResources(user_pool, domain, resource_server, client)

    def _create_runtime(
        self,
        prefix: str,
        runtime_name: str,
        asset_path: str,
        protocol: ProtocolType,
        auth_pool: UserPoolResources,
        ssm_param_name: str,
    ) -> RuntimeResources:
        """Create an AgentCore runtime with its own execution role, artifact, and SSM param."""
        role = iam.Role(
            self,
            f"{prefix}ExecutionRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            inline_policies={
                "BasePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["ssm:GetParameter"],
                            resources=[
                                f"arn:aws:ssm:{self.region}:{self.account}:parameter/agentcore/*"
                            ],
                        ),
                        iam.PolicyStatement(
                            actions=["secretsmanager:GetSecretValue"],
                            resources=[
                                f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:agentcore/*"
                            ],
                        ),
                    ]
                ),
            },
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"),
            ],
        )

        artifact = AgentRuntimeArtifact.from_asset(
            os.path.join(os.path.dirname(__file__), "..", asset_path)
        )

        runtime = Runtime(
            self,
            f"{prefix}Runtime",
            runtime_name=runtime_name,
            execution_role=role,
            agent_runtime_artifact=artifact,
            protocol_configuration=protocol,
            authorizer_configuration=RuntimeAuthorizerConfiguration.using_cognito(
                auth_pool.user_pool,
                [auth_pool.client],
            ),
        )

        ssm.StringParameter(
            self,
            f"{prefix}RuntimeArnParam",
            parameter_name=ssm_param_name,
            string_value=runtime.agent_runtime_arn,
        )

        return RuntimeResources(runtime, role)

    def _create_gateway(
        self,
        prefix: str,
        gateway_name: str,
        authorizer_configuration: GatewayAuthorizer,
        ssm_param_name: str,
        credential_provider_name: str,
    ) -> Gateway:
        """Create an AgentCore gateway with OAuth role permissions and SSM param for its URL."""
        gw = Gateway(
            self,
            f"{prefix}Gateway",
            gateway_name=gateway_name,
            authorizer_configuration=authorizer_configuration,
        )

        # Service role permissions for the OAuth credential provider flow
        workload_identity_base = f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:workload-identity-directory/default"
        token_vault_base = f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:token-vault/default"
        gw.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:CompleteResourceTokenAuth",
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetResourceOauth2Token",
                ],
                resources=[
                    workload_identity_base,
                    f"{workload_identity_base}/workload-identity/{gateway_name}-*",
                    token_vault_base,
                    f"{token_vault_base}/oauth2credentialprovider/{credential_provider_name}",
                ],
            )
        )

        gateway_url = f"https://{gw.gateway_id}.gateway.bedrock-agentcore.{self.region}.amazonaws.com/mcp"

        ssm.StringParameter(
            self,
            f"{prefix}GatewayUrlParam",
            parameter_name=ssm_param_name,
            string_value=gateway_url,
        )

        return gw

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------
        # Cognito User Pools
        # ---------------------------------------------------------------

        # Agent Cognito User Pool — authenticates requests to the agent runtime
        agent_auth = self._create_user_pool(
            prefix="Agent",
            pool_name="agentcore-agent-user-pool",
            domain_prefix="agentcore-agent",
            resource_server_id="agent",
            scope_description="Invoke agent runtime",
            secret_name="agentcore/agent-cognito",
        )

        # JWT Gateway Cognito User Pool — authenticates inbound gateway requests
        gateway_auth = self._create_user_pool(
            prefix="JwtGateway",
            pool_name="agentcore-gateway-pool",
            domain_prefix="agentcore-gateway",
            resource_server_id="gateway",
            scope_description="Invoke AgentCore Gateway",
            secret_name="agentcore/jwt-gateway-cognito",
        )

        # MCP Cognito User Pool — authenticates requests to MCP runtimes
        mcp_auth = self._create_user_pool(
            prefix="Mcp",
            pool_name="agentcore-mcp-user-pool",
            domain_prefix="agentcore-mcp",
            resource_server_id="mcp",
            scope_description="Invoke MCP runtimes",
            secret_name="agentcore/mcp-cognito",
        )

        # ---------------------------------------------------------------
        # OAuth2 Credential Provider — stores MCP Cognito credentials in AgentCore Identity
        # ---------------------------------------------------------------
        mcp_oauth_provider_name = "mcp-runtime-oauth-provider"
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

        # ---------------------------------------------------------------
        # Agent Runtimes
        # ---------------------------------------------------------------

        # Agent Runtime — Bedrock-powered agent that calls MCP tools
        agent_rt = self._create_runtime(
            prefix="AgentRuntime",
            runtime_name="agent_runtime",
            asset_path="agent",
            protocol=ProtocolType.HTTP,
            auth_pool=agent_auth,
            ssm_param_name="/agentcore/agent-runtime-arn",
        )

        # ---------------------------------------------------------------
        # MCP Runtimes
        # ---------------------------------------------------------------
        
        # MCP Calculator Runtime — hosts the calculator MCP server
        mcp_rt = self._create_runtime(
            prefix="McpCalculator",
            runtime_name="mcp_calculator",
            asset_path="mcp/calculator",
            protocol=ProtocolType.MCP,
            auth_pool=mcp_auth,
            ssm_param_name="/agentcore/mcp-calculator-runtime-arn",
        )

        # URL-encode the runtime ARN for the invocation endpoint
        escaped_arn = cdk.Fn.join(
            "%2F",
            cdk.Fn.split(
                "/",
                cdk.Fn.join("%3A", cdk.Fn.split(":", mcp_rt.runtime.agent_runtime_arn)),
            ),
        )
        mcp_calculator_runtime_endpoint = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{escaped_arn}/invocations?qualifier=DEFAULT"

        # ---------------------------------------------------------------
        # MCP Lambda Targets
        # ---------------------------------------------------------------
        
        temperature_lambda = lambda_.DockerImageFunction(
            self,
            "McpTemperatureConverter",
            function_name="mcp_temperature_converter",
            architecture=lambda_.Architecture.ARM_64,
            code=lambda_.DockerImageCode.from_image_asset(
                os.path.join(os.path.dirname(__file__), "..", "mcp", "temperature_converter"),
                platform=ecr_assets.Platform.LINUX_ARM64,
            ),
        )
        
        # ---------------------------------------------------------------
        # Gateways
        # ---------------------------------------------------------------

        # JWT Gateway — Cognito-authenticated MCP gateway
        jwt_gateway = self._create_gateway(
            prefix="Jwt",
            gateway_name="agentcore-jwt-gateway",
            authorizer_configuration=GatewayAuthorizer.using_cognito(
                user_pool=gateway_auth.user_pool,
                allowed_clients=[gateway_auth.client],
            ),
            ssm_param_name="/agentcore/jwt-gateway-url",
            credential_provider_name=mcp_oauth_provider_name,
        )

        # IAM Gateway — SigV4-authenticated MCP gateway
        iam_gateway = self._create_gateway(
            prefix="Iam",
            gateway_name="agentcore-iam-gateway",
            authorizer_configuration=GatewayAuthorizer.using_aws_iam(),
            ssm_param_name="/agentcore/iam-gateway-url",
            credential_provider_name=mcp_oauth_provider_name,
        )

        # Grant the agent runtime's execution role permission to invoke the IAM gateway
        # The JWT gateway uses Cognito auth, authorisation is determined entirely by whether your Bearer token is valid
        agent_rt.role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock-agentcore:InvokeGateway"],
                resources=[
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:gateway/{iam_gateway.gateway_id}"
                ],
            )
        )

        # ---------------------------------------------------------------
        # Gateway Targets
        # ---------------------------------------------------------------
        mcp_credential_provider = GatewayCredentialProvider.from_oauth_identity_arn(
            provider_arn=mcp_oauth_provider_arn,
            secret_arn=mcp_oauth_secret_arn,
            scopes=["mcp/invoke"],
        )

        # MCP Calculator target — IAM gateway only
        iam_gateway.add_mcp_server_target(
            "CalculatorTarget",
            gateway_target_name="calculator",
            description="MCP Calculator runtime",
            endpoint=mcp_calculator_runtime_endpoint,
            credential_provider_configurations=[mcp_credential_provider],
        )

        # Temperature Converter Lambda — JWT gateway only
        jwt_gateway.add_lambda_target(
            "TemperatureConverterTarget",
            gateway_target_name="temperature-converter",
            description="Temperature conversion tools (Celsius <> Fahrenheit)",
            lambda_function=temperature_lambda,
            tool_schema=ToolSchema.from_local_asset(
                os.path.join(
                    os.path.dirname(__file__), "..", "mcp", "temperature_converter", "schema.json"
                )
            ),
        )

        # ---------------------------------------------------------------
        # Stack Outputs
        # ---------------------------------------------------------------
        iam_gateway_url = f"https://{iam_gateway.gateway_id}.gateway.bedrock-agentcore.{self.region}.amazonaws.com/mcp"
        jwt_gateway_url = f"https://{jwt_gateway.gateway_id}.gateway.bedrock-agentcore.{self.region}.amazonaws.com/mcp"
        cdk.CfnOutput(self, "IamGatewayUrl", value=iam_gateway_url)
        cdk.CfnOutput(self, "JwtGatewayUrl", value=jwt_gateway_url)
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
        cdk.CfnOutput(
            self, "AgentCalculatorRuntimeArn", value=agent_rt.runtime.agent_runtime_arn
        )
        cdk.CfnOutput(
            self, "McpCalculatorRuntimeArn", value=mcp_rt.runtime.agent_runtime_arn
        )
        cdk.CfnOutput(self, "McpOAuthProviderArn", value=mcp_oauth_provider_arn)
        cdk.CfnOutput(self, "McpOAuthSecretArn", value=mcp_oauth_secret_arn)
