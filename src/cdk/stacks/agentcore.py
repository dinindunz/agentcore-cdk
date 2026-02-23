import os

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk.aws_bedrock_agentcore_alpha import ProtocolType, GatewayAuthorizer
from constructs import Construct

from ..config import config
from ..constructs import (
    BucketDeploymentConstruct,
    LambdaTargetConstruct,
    McpServerTargetConstruct,
    OpenApiTargetConstruct,
    UserPoolConstruct,
    RuntimeConstruct,
    GatewayConstruct,
    OAuth2CredentialProviderConstruct,
    ApiKeyCredentialProviderConstruct,
)
from ..utils import DestroyLogGroups, LogGroupCleanup, to_kebab_case, to_snake_case


class AgentCoreStack(cdk.Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Ensure all log groups in this stack are cleaned up on deletion
        cdk.Aspects.of(self).add(DestroyLogGroups())

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
        # AgentCore Identity — Credential Providers
        # ---------------------------------------------------------------

        # OAuth2 Credential Provider — Stores MCP Cognito credentials for authenticating to MCP AgentCore runtimes
        mcp_oauth = OAuth2CredentialProviderConstruct(
            self,
            "McpOAuthCredentialProvider",
            provider_name="mcp-runtime-oauth-provider",
            user_pool=mcp_auth,
            scopes=["mcp/invoke"],
        )

        # API Key Credential Provider — Stores GitHub PAT
        github_api_key = ApiKeyCredentialProviderConstruct(
            self,
            "GithubApiKeyCredentialProvider",
            provider_name="github-api-key-provider",
            api_key=os.environ["GITHUB_TOKEN"],
        )

        # ---------------------------------------------------------------
        # Skills — deployed to S3 for agent to search skills
        # ---------------------------------------------------------------

        skills_bucket = BucketDeploymentConstruct(
            self,
            "SkillsBucket",
            bucket_name="skills",
            source_path="skills",
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
            api_key_provider_names=[github_api_key.name],
        )

        # IAM Gateway — SigV4-authenticated MCP gateway
        iam_gw = GatewayConstruct(
            self,
            "IamGateway",
            gateway_name="iam-gateway",
            authorizer_configuration=GatewayAuthorizer.using_aws_iam(),
            oauth2_provider_names=[mcp_oauth.name],
        )

        # ---------------------------------------------------------------
        # AgentCore Runtimes
        # ---------------------------------------------------------------

        # Build agent runtime environment variables
        agent_env_vars = {
            "REGION_NAME": self.region,
            "JWT_GATEWAY_SSM_PATH": jwt_gw.ssm_url_param_name,
            "IAM_GATEWAY_SSM_PATH": iam_gw.ssm_url_param_name,
            "GATEWAY_COGNITO_SECRET": gateway_auth.secret_name,
            "SKILLS_BUCKET": skills_bucket.bucket_name_value,
        }

        # Add observability configuration if enabled
        if config.enable_observability:
            # Get observability stack prefix
            obs_stack_prefix = self._get_observability_stack_prefix()

            # Lookup observability endpoints/secrets from SSM (no cross-stack dependency)
            from aws_cdk import aws_ssm as ssm

            otel_endpoint = ssm.StringParameter.value_from_lookup(
                self, f"/{obs_stack_prefix}/otel-endpoint"
            )
            phoenix_secret_arn = ssm.StringParameter.value_from_lookup(
                self, f"/{obs_stack_prefix}/phoenix-api-key-secret-arn"
            )

            agent_env_vars.update(
                {
                    # OTEL endpoint (read from SSM at synthesis time)
                    "OTEL_EXPORTER_OTLP_ENDPOINT": otel_endpoint,
                    # OTLP configuration
                    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
                    "OTEL_TRACES_EXPORTER": "otlp",
                    "OTEL_METRICS_EXPORTER": "none",
                    "OTEL_LOGS_EXPORTER": "none",
                    # Service identification
                    "OTEL_SERVICE_NAME": f"{stack_prefix}-agent",
                    "OTEL_RESOURCE_ATTRIBUTES": f"project.name={stack_prefix}",
                    # Disable AWS configurator to allow standard OTLP
                    "OTEL_PYTHON_CONFIGURATOR": "default_configurator",
                    # Phoenix API key secret ARN (read from SSM at synthesis time)
                    "PHOENIX_API_KEY_SECRET_ARN": phoenix_secret_arn,
                }
            )

        # Agent Runtime — the "agent" runtime that will orchestrate calls to the gateways and execute tools
        agent_rt = RuntimeConstruct(
            self,
            "AgentRuntime",
            runtime_name="agent",
            asset_path="agent",
            protocol=ProtocolType.HTTP,
            auth_pool=agent_auth,
            environment_variables=agent_env_vars,
        )

        # Grant the agent runtime's execution role permission to read skills from S3
        skills_bucket.bucket.grant_read(agent_rt.role)

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

        # Grant agent runtime permission to read Phoenix API key if observability is enabled
        if config.enable_observability:
            # Grant access to Phoenix secret using ARN pattern (no cross-stack reference)
            from aws_cdk import aws_ssm as ssm

            obs_stack_prefix = self._get_observability_stack_prefix()
            phoenix_secret_arn = ssm.StringParameter.value_from_lookup(
                self, f"/{obs_stack_prefix}/phoenix-api-key-secret-arn"
            )

            agent_rt.role.add_to_policy(
                iam.PolicyStatement(
                    actions=["secretsmanager:GetSecretValue"],
                    resources=[phoenix_secret_arn],
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

        # ---------------------------------------------------------------
        # Gateway Targets
        # ---------------------------------------------------------------

        # Skill Search — keyword search over skill definitions stored in S3, on IAM Gateway
        skill_search = LambdaTargetConstruct(
            self,
            "SkillSearchLambda",
            asset_path="mcp/skill_search",
            gateway=iam_gw,
            target_name="skill-search",
            description="Search available agent skills by keyword",
            environment={"SKILLS_BUCKET": skills_bucket.bucket_name_value},
        )
        skills_bucket.bucket.grant_read(skill_search.function)

        # MCP Calculator Runtime Target on IAM Gateway
        McpServerTargetConstruct(
            self,
            "CalculatorTarget",
            gateway=iam_gw,
            target_name="calculator",
            description="Calculator tools (add, subtract, multiply, divide)",
            endpoint=mcp_calculator_rt.endpoint,
            credential_provider_configurations=[mcp_oauth.credential_provider],
        )

        # Temperature Converter — Celsius <> Fahrenheit conversion tools on JWT Gateway
        LambdaTargetConstruct(
            self,
            "McpTemperatureConverter",
            asset_path="mcp/temperature_converter",
            gateway=jwt_gw,
            target_name="temperature-converter",
            description="Temperature conversion tools (Celsius <> Fahrenheit)",
        )

        # GitHub Open API Target on JWT Gateway
        OpenApiTargetConstruct(
            self,
            "GithubTarget",
            gateway=jwt_gw,
            target_name="github",
            description="GitHub API tools (repos, issues, pull requests, search)",
            schema_path="mcp/github/schema.json",
            credential_provider_configurations=[github_api_key.credential_provider],
        )

        # Log group cleanup — deletes orphaned log groups on stack destruction
        cleanup = LogGroupCleanup(
            self,
            "LogGroupCleanup",
            log_group_prefixes=[
                f"/aws/bedrock-agentcore/runtimes/{to_snake_case(self.stack_name)}_",
                f"/aws/lambda/{self.stack_name}-",
                f"/aws/lambda/{stack_prefix}-",
            ],
        )

        # Ensure cleanup runs last during stack deletion (reverse dependency order)
        for construct in [mcp_oauth, github_api_key, agent_rt, mcp_calculator_rt]:
            construct.node.add_dependency(cleanup.resource)

        # ---------------------------------------------------------------
        # Stack Outputs
        # ---------------------------------------------------------------
        cdk.CfnOutput(self, "IamGatewayUrl", value=iam_gw.url)
        cdk.CfnOutput(self, "JwtGatewayUrl", value=jwt_gw.url)
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

    def _get_observability_stack_prefix(self) -> str:
        """Get the observability stack prefix based on environment."""
        env_suffix = self.stack_name.split("-")[-1]  # Extract 'dev', 'test', etc
        obs_stack_name = f"ObservabilityStack-{env_suffix}"
        return to_kebab_case(obs_stack_name)
