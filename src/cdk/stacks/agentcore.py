import os

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_logs as logs
from aws_cdk.aws_bedrock_agentcore_alpha import (
    ApiSchema,
    ProtocolType,
    GatewayAuthorizer,
    ToolSchema,
)
from constructs import Construct

from ..constructs import (
    UserPoolConstruct,
    RuntimeConstruct,
    GatewayConstruct,
    OAuth2CredentialProviderConstruct,
    ApiKeyCredentialProviderConstruct,
)
from ..utils import DestroyLogGroups, to_kebab_case, to_snake_case


class AgentCoreStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
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

        # Agent Runtime — the "agent" runtime that will orchestrate calls to the gateways and execute tools
        agent_rt = RuntimeConstruct(
            self,
            "AgentRuntime",
            runtime_name="agent",
            asset_path="agent",
            protocol=ProtocolType.HTTP,
            auth_pool=agent_auth,
            environment_variables={
                "REGION_NAME": self.region,
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
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "mcp",
                    "temperature_converter",
                ),
                platform=ecr_assets.Platform.LINUX_ARM64,
            ),
        )

        # Grant the JWT gateway's service role permission to invoke the temperature converter Lambda
        # (the L2 add_lambda_target does not auto-grant this)
        temperature_lambda.grant_invoke(jwt_gw.gateway.role)

        # ---------------------------------------------------------------
        # Gateway Targets
        # ---------------------------------------------------------------

        # MCP Calculator Runtime Target to IAM Gateway
        iam_gw.gateway.add_mcp_server_target(
            "CalculatorTarget",
            gateway_target_name="calculator",
            description="Calculator tools (add, subtract, multiply, divide)",
            endpoint=mcp_calculator_rt.endpoint,
            credential_provider_configurations=[mcp_oauth.credential_provider],
        )

        # Temperature Converter Lambda Target to JWT Gateway
        temp_target = jwt_gw.gateway.add_lambda_target(
            "TemperatureConverterTarget",
            gateway_target_name="temperature-converter",
            description="Temperature conversion tools (Celsius <> Fahrenheit)",
            lambda_function=temperature_lambda,
            tool_schema=ToolSchema.from_local_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "mcp",
                    "temperature_converter",
                    "schema.json",
                )
            ),
        )
        # Ensure the gateway's service role policy (with lambda:InvokeFunction) is created
        # before the target — AgentCore validates this at CreateGatewayTarget time
        if jwt_gw.gateway.role.node.try_find_child("DefaultPolicy"):
            temp_target.node.add_dependency(
                jwt_gw.gateway.role.node.find_child("DefaultPolicy")
            )

        # GitHub REST API Target to JWT Gateway
        jwt_gw.gateway.add_open_api_target(
            "GithubTarget",
            gateway_target_name="github",
            description="GitHub API tools (repos, issues, pull requests, search)",
            api_schema=ApiSchema.from_local_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "mcp",
                    "github",
                    "schema.json",
                )
            ),
            credential_provider_configurations=[github_api_key.credential_provider],
        )

        # ---------------------------------------------------------------
        # Log group cleanup — delete service-managed log groups on stack deletion
        # (AgentCore runtimes, ECR deployment, and AwsCustomResource Lambdas
        # create log groups outside CloudFormation)
        # ---------------------------------------------------------------
        log_group_prefixes = [
            f"/aws/bedrock-agentcore/runtimes/{to_snake_case(self.stack_name)}_",
            f"/aws/lambda/{self.stack_name}-",
            f"/aws/lambda/{stack_prefix}-",
        ]

        # Explicit LogGroup so CloudFormation deletes it on stack destruction
        # (prevents the cleanup Lambda's own log group from being orphaned)
        cleanup_fn_name = f"{stack_prefix}-log-cleanup"
        cleanup_log_group = logs.LogGroup(
            self,
            "LogGroupCleanupLogs",
            log_group_name=f"/aws/lambda/{cleanup_fn_name}",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Handle CFN custom resource protocol directly — avoids the extra
        # framework Lambda that cr.Provider creates (another orphaned log group)
        cleanup_fn = lambda_.Function(
            self,
            "LogGroupCleanupFn",
            function_name=cleanup_fn_name,
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=cleanup_log_group,
            code=lambda_.Code.from_inline(
                "import json, urllib.request, boto3\n"
                "def handler(event, context):\n"
                "    status, reason = 'SUCCESS', ''\n"
                "    pid = event.get('PhysicalResourceId', context.log_stream_name)\n"
                "    try:\n"
                "        if event['RequestType'] == 'Delete':\n"
                "            client = boto3.client('logs')\n"
                "            exclude = set(event['ResourceProperties'].get('Exclude', []))\n"
                "            for prefix in event['ResourceProperties']['Prefixes']:\n"
                "                paginator = client.get_paginator('describe_log_groups')\n"
                "                for page in paginator.paginate(logGroupNamePrefix=prefix):\n"
                "                    for lg in page['logGroups']:\n"
                "                        name = lg['logGroupName']\n"
                "                        if name not in exclude:\n"
                "                            client.delete_log_group(logGroupName=name)\n"
                "    except Exception as e:\n"
                "        print(e)\n"
                "        status, reason = 'FAILED', str(e)\n"
                "    body = json.dumps({'Status': status, 'Reason': reason or 'See CloudWatch',\n"
                "        'PhysicalResourceId': pid, 'StackId': event['StackId'],\n"
                "        'RequestId': event['RequestId'],\n"
                "        'LogicalResourceId': event['LogicalResourceId']}).encode()\n"
                "    req = urllib.request.Request(event['ResponseURL'], data=body, method='PUT')\n"
                "    req.add_header('Content-Type', '')\n"
                "    urllib.request.urlopen(req)\n"
            ),
            timeout=cdk.Duration.minutes(5),
        )
        cleanup_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:DescribeLogGroups"],
                resources=["*"],
            )
        )
        cleanup_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:DeleteLogGroup"],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:{prefix}*"
                    for prefix in log_group_prefixes
                ],
            )
        )
        cleanup_fn.add_permission(
            "CfnInvoke",
            principal=iam.ServicePrincipal("cloudformation.amazonaws.com"),
        )

        cleanup = cdk.CustomResource(
            self,
            "LogGroupCleanup",
            service_token=cleanup_fn.function_arn,
            properties={
                "Prefixes": log_group_prefixes,
                # Skip our own log group — it's CFN-managed via cleanup_log_group
                "Exclude": [f"/aws/lambda/{cleanup_fn_name}"],
            },
        )

        # Make constructs with custom-resource Lambdas depend on the cleanup resource.
        # During deletion (reverse order), their Lambdas finish first, then cleanup
        # runs last and deletes all orphaned log groups.
        for construct in [mcp_oauth, github_api_key, agent_rt, mcp_calculator_rt]:
            construct.node.add_dependency(cleanup)

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
