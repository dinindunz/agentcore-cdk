import os

import aws_cdk as cdk
from aws_cdk import aws_iam as iam

# TODO: Refactor to use aws_cdk once L2 constructs are available.
from aws_cdk.aws_bedrock_agentcore_alpha import GatewayAuthorizer, ProtocolType
from constructs import Construct

# Import evaluator definitions
from ...evals import (
    github_integrity,
    math_accuracy,
    output_format,
    skill_workflow,
    temperature_conversion,
)
from ..constructs import (
    ApiKeyCredentialProviderConstruct,
    BucketDeploymentConstruct,
    CustomEvaluatorConstruct,
    GatewayConstruct,
    LambdaTargetConstruct,
    McpServerTargetConstruct,
    MemoryConstruct,
    ModelConfiguration,
    OAuth2CredentialProviderConstruct,
    OnlineEvaluationConstruct,
    OpenApiTargetConstruct,
    RuntimeConstruct,
    ScoringSchemaDefinition,
    UserPoolConstruct,
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
        # Create Memory
        # ---------------------------------------------------------------
        self.memory = MemoryConstruct(
            self,
            "AgentMemory",
            memory_name="agent-memory",
            event_expiry_days=90,
            enable_summary_strategy=True,
            enable_preference_strategy=True,
            enable_semantic_strategy=True,
            enable_episodic_strategy=False,  # TODO: Disabled - Fix configuration issues
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
            "MEMORY_ID": self.memory.memory_id,
            "LOG_LEVEL": "INFO",  # Configurable logging level (DEBUG, INFO, WARNING, ERROR)
        }

        # Agent Runtime — the "agent" runtime that will orchestrate calls to the gateways and execute tools
        agent_rt = RuntimeConstruct(
            self,
            "AgentRuntime",
            runtime_name="agent",
            asset_path="agent",
            protocol=ProtocolType.HTTP,
            auth_pool=agent_auth,
            environment_variables=agent_env_vars,
            enable_observability=True,
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

        # Grant agent runtime permissions to use memory
        agent_rt.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:CreateEvent",
                    "bedrock-agentcore:ListEvents",
                    "bedrock-agentcore:GetEvent",
                    "bedrock-agentcore:ListSessions",
                    "bedrock-agentcore:RetrieveMemoryRecords",
                    "bedrock-agentcore:GetMemoryRecord",
                    "bedrock-agentcore:ListMemoryRecords",
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:memory/{self.memory.memory_id}",
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:memory/{self.memory.memory_id}/*",
                ],
            )
        )

        # ---------------------------------------------------------------
        # Custom Evaluators — domain-specific validation
        # ---------------------------------------------------------------

        # Math Accuracy Evaluator (tool level)
        math_eval = CustomEvaluatorConstruct(
            self,
            "MathAccuracyEvaluator",
            evaluator_name=math_accuracy.EVALUATOR_NAME,
            evaluation_level=math_accuracy.EVALUATION_LEVEL,
            prompt=math_accuracy.PROMPT,
            scoring_schema=ScoringSchemaDefinition.numbered_scale(
                min_value=math_accuracy.MIN_VALUE,
                max_value=math_accuracy.MAX_VALUE,
                description=math_accuracy.SCORING_DESCRIPTION,
            ),
            model_config=ModelConfiguration(
                model_id=math_accuracy.MODEL_ID,
                temperature=math_accuracy.TEMPERATURE,
                top_p=math_accuracy.TOP_P,
                max_tokens=math_accuracy.MAX_TOKENS,
            ),
            description=math_accuracy.DESCRIPTION,
        )

        # Temperature Conversion Evaluator (tool level)
        temp_conversion_eval = CustomEvaluatorConstruct(
            self,
            "TemperatureConversionEvaluator",
            evaluator_name=temperature_conversion.EVALUATOR_NAME,
            evaluation_level=temperature_conversion.EVALUATION_LEVEL,
            prompt=temperature_conversion.PROMPT,
            scoring_schema=ScoringSchemaDefinition.binary(
                description=temperature_conversion.SCORING_DESCRIPTION
            ),
            model_config=ModelConfiguration(
                model_id=temperature_conversion.MODEL_ID,
                temperature=temperature_conversion.TEMPERATURE,
                top_p=temperature_conversion.TOP_P,
                max_tokens=temperature_conversion.MAX_TOKENS,
            ),
            description=temperature_conversion.DESCRIPTION,
        )

        # Skill Workflow Evaluator (trace level)
        skill_workflow_eval = CustomEvaluatorConstruct(
            self,
            "SkillWorkflowEvaluator",
            evaluator_name=skill_workflow.EVALUATOR_NAME,
            evaluation_level=skill_workflow.EVALUATION_LEVEL,
            prompt=skill_workflow.PROMPT,
            scoring_schema=ScoringSchemaDefinition.numbered_scale(
                min_value=skill_workflow.MIN_VALUE,
                max_value=skill_workflow.MAX_VALUE,
                description=skill_workflow.SCORING_DESCRIPTION,
            ),
            model_config=ModelConfiguration(
                model_id=skill_workflow.MODEL_ID,
                temperature=skill_workflow.TEMPERATURE,
                top_p=skill_workflow.TOP_P,
                max_tokens=skill_workflow.MAX_TOKENS,
            ),
            description=skill_workflow.DESCRIPTION,
        )

        # GitHub Data Integrity Evaluator (trace level)
        github_integrity_eval = CustomEvaluatorConstruct(
            self,
            "GitHubIntegrityEvaluator",
            evaluator_name=github_integrity.EVALUATOR_NAME,
            evaluation_level=github_integrity.EVALUATION_LEVEL,
            prompt=github_integrity.PROMPT,
            scoring_schema=ScoringSchemaDefinition.numbered_scale(
                min_value=github_integrity.MIN_VALUE,
                max_value=github_integrity.MAX_VALUE,
                description=github_integrity.SCORING_DESCRIPTION,
            ),
            model_config=ModelConfiguration(
                model_id=github_integrity.MODEL_ID,
                temperature=github_integrity.TEMPERATURE,
                top_p=github_integrity.TOP_P,
                max_tokens=github_integrity.MAX_TOKENS,
            ),
            description=github_integrity.DESCRIPTION,
        )

        # Output Format Evaluator (trace level)
        output_format_eval = CustomEvaluatorConstruct(
            self,
            "OutputFormatEvaluator",
            evaluator_name=output_format.EVALUATOR_NAME,
            evaluation_level=output_format.EVALUATION_LEVEL,
            prompt=output_format.PROMPT,
            scoring_schema=ScoringSchemaDefinition.binary(
                description=output_format.SCORING_DESCRIPTION
            ),
            model_config=ModelConfiguration(
                model_id=output_format.MODEL_ID,
                temperature=output_format.TEMPERATURE,
                top_p=output_format.TOP_P,
                max_tokens=output_format.MAX_TOKENS,
            ),
            description=output_format.DESCRIPTION,
        )

        # ---------------------------------------------------------------
        # Online Evaluation — continuous monitoring with built-in + custom evaluators
        # ---------------------------------------------------------------

        agent_eval = OnlineEvaluationConstruct(
            self,
            "AgentOnlineEvaluation",
            config_name=f"{agent_rt.runtime.agent_runtime_name}",
            runtime=agent_rt,
            evaluators=[
                # Built-in evaluators (LLM-as-judge for general quality) - max 10 total
                "Builtin.Helpfulness",
                "Builtin.Correctness",
                "Builtin.ToolSelectionAccuracy",
                "Builtin.ToolParameterAccuracy",
                "Builtin.ResponseRelevance",
                # Custom evaluators (domain-specific validation)
                math_eval.to_evaluator_reference(),
                temp_conversion_eval.to_evaluator_reference(),
                skill_workflow_eval.to_evaluator_reference(),
                github_integrity_eval.to_evaluator_reference(),
                output_format_eval.to_evaluator_reference(),
            ],
            sampling_rate=100.0,  # Evaluate 100% of interactions
            description="Comprehensive evaluation with built-in + custom evaluators",
            enable_on_create=True,
        )

        # MCP Calculator Runtime — a simple MCP runtime that exposes calculator tools (add, subtract, multiply, divide) for demonstration purposes
        mcp_calculator_rt = RuntimeConstruct(
            self,
            "McpCalculatorRuntime",
            runtime_name="mcp_calculator",
            asset_path="mcp/calculator",
            protocol=ProtocolType.MCP,
            auth_pool=mcp_auth,
            environment_variables={"LOG_LEVEL": "INFO"},
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
            environment={
                "SKILLS_BUCKET": skills_bucket.bucket_name_value,
                "LOG_LEVEL": "INFO",
            },
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
            environment={"LOG_LEVEL": "INFO"},
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
                "/aws/bedrock-agentcore/evaluations/",
                f"/aws/lambda/{self.stack_name}-",
                f"/aws/lambda/{stack_prefix}-",
            ],
        )

        # Ensure cleanup runs last during stack deletion (reverse dependency order)
        for construct in [
            mcp_oauth,
            github_api_key,
            agent_rt,
            mcp_calculator_rt,
            agent_eval,
        ]:
            construct.node.add_dependency(cleanup.resource)

        # ---------------------------------------------------------------
        # Stack Outputs
        # ---------------------------------------------------------------
        cdk.CfnOutput(self, "IamGatewayUrl", value=iam_gw.url)
        cdk.CfnOutput(self, "JwtGatewayUrl", value=jwt_gw.url)
        cdk.CfnOutput(self, "JwtGatewayUserPoolId", value=gateway_auth.user_pool.user_pool_id)
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
        cdk.CfnOutput(self, "AgentUserPoolClientId", value=agent_auth.client.user_pool_client_id)
        cdk.CfnOutput(
            self,
            "AgentTokenEndpoint",
            value=f"{agent_auth.domain.base_url()}/oauth2/token",
        )
        cdk.CfnOutput(self, "McpUserPoolId", value=mcp_auth.user_pool.user_pool_id)
        cdk.CfnOutput(self, "McpUserPoolClientId", value=mcp_auth.client.user_pool_client_id)
        cdk.CfnOutput(self, "McpTokenEndpoint", value=f"{mcp_auth.domain.base_url()}/oauth2/token")
        cdk.CfnOutput(self, "AgentRuntimeArn", value=agent_rt.runtime.agent_runtime_arn)
        cdk.CfnOutput(
            self,
            "McpCalculatorRuntimeArn",
            value=mcp_calculator_rt.runtime.agent_runtime_arn,
        )
        cdk.CfnOutput(
            self,
            "AgentEvaluationConfigId",
            value=agent_eval.config_id,
            description="Online evaluation configuration ID",
        )
