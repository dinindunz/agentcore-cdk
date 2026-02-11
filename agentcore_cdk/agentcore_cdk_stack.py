import os

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_bedrock_agentcore_alpha import (
    AgentRuntimeArtifact,
    Runtime,
    RuntimeAuthorizerConfiguration,
    ProtocolType,
    Gateway,
    GatewayAuthorizer,
)
from constructs import Construct


class AgentcoreCdkStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role = iam.Role(
            self, "AgentRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
        )

        role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=["*"],
            )
        )

        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess")
        )

        role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/agentcore/*"],
            )
        )

        role.add_to_policy(
            iam.PolicyStatement(
                actions=["cognito-idp:DescribeUserPoolClient"],
                resources=[f"arn:aws:cognito-idp:{self.region}:{self.account}:userpool/*"],
            )
        )

        gateway = Gateway(
            self, "McpGateway",
            gateway_name="agentcoreMcpGateway",
            authorizer_configuration=GatewayAuthorizer.using_aws_iam(),
        )

        # Cognito User Pool for Runtime auth
        user_pool = cognito.UserPool(
            self, "AgentCoreUserPool",
            user_pool_name="agentcore-user-pool",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        user_pool_domain = user_pool.add_domain(
            "AgentCoreUserPoolDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="agentcore-mcp",
            ),
        )

        resource_server = user_pool.add_resource_server(
            "AgentCoreResourceServer",
            identifier="agentcore",
            scopes=[
                cognito.ResourceServerScope(scope_name="invoke", scope_description="Invoke AgentCore runtimes"),
            ],
        )

        user_pool_client = user_pool.add_client(
            "AgentCoreUserPoolClient",
            generate_secret=True,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(client_credentials=True),
                scopes=[cognito.OAuthScope.resource_server(resource_server, cognito.ResourceServerScope(scope_name="invoke", scope_description="Invoke AgentCore runtimes"))],
            ),
        )

        mcp_calculator_runtime_artifact = AgentRuntimeArtifact.from_asset(
            os.path.join(os.path.dirname(__file__), "..", "mcp-calculator")
        )

        mcp_calculator_runtime = Runtime(
            self, "McpCalculator",
            runtime_name="mcpCalculator",
            execution_role=role,
            agent_runtime_artifact=mcp_calculator_runtime_artifact,
            protocol_configuration=ProtocolType.MCP,
            authorizer_configuration=RuntimeAuthorizerConfiguration.using_cognito(
                user_pool, [user_pool_client],
            ),
        )

        agent_runtime_artifact = AgentRuntimeArtifact.from_asset(
            os.path.join(os.path.dirname(__file__), "..", "agent")
        )

        agent_runtime = Runtime(
            self, "Agent",
            runtime_name="agent",
            execution_role=role,
            agent_runtime_artifact=agent_runtime_artifact,
            protocol_configuration=ProtocolType.HTTP,
            authorizer_configuration=RuntimeAuthorizerConfiguration.using_cognito(
                user_pool, [user_pool_client],
            ),
        )

        ssm.StringParameter(
            self, "McpCalculatorRuntimeArnParam",
            parameter_name="/agentcore/mcp-calculator-runtime-arn",
            string_value=mcp_calculator_runtime.agent_runtime_arn,
        )

        ssm.StringParameter(
            self, "AgentRuntimeArnParam",
            parameter_name="/agentcore/agent-runtime-arn",
            string_value=agent_runtime.agent_runtime_arn,
        )

        ssm.StringParameter(
            self, "CognitoClientIdParam",
            parameter_name="/agentcore/cognito-client-id",
            string_value=user_pool_client.user_pool_client_id,
        )

        ssm.StringParameter(
            self, "CognitoUserPoolIdParam",
            parameter_name="/agentcore/cognito-user-pool-id",
            string_value=user_pool.user_pool_id,
        )

        ssm.StringParameter(
            self, "CognitoTokenEndpointParam",
            parameter_name="/agentcore/cognito-token-endpoint",
            string_value=f"{user_pool_domain.base_url()}/oauth2/token",
        )

        cdk.CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        cdk.CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
        cdk.CfnOutput(self, "CognitoIssuer", value=f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool.user_pool_id}")
        cdk.CfnOutput(self, "AuthorizationEndpoint", value=f"{user_pool_domain.base_url()}/oauth2/authorize")
        cdk.CfnOutput(self, "TokenEndpoint", value=f"{user_pool_domain.base_url()}/oauth2/token")
        cdk.CfnOutput(self, "McpCalculatorRuntimeArn", value=mcp_calculator_runtime.agent_runtime_arn)
        cdk.CfnOutput(self, "AgentRuntimeArn", value=agent_runtime.agent_runtime_arn)
