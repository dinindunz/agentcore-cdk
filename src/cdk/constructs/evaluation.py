import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import custom_resources as cr
from constructs import Construct

from ..utils import to_snake_case
from .runtime import RuntimeConstruct


# TODO: Refactor to use L2 constructs once they are available.
class OnlineEvaluationConstruct(Construct):
    """Creates an AgentCore online evaluation configuration.

    Example:
        evaluation = OnlineEvaluationConstruct(
            self, "AgentEvaluation",
            config_name="agent_quality",
            runtime=agent_runtime,
            evaluators=[
                "Builtin.Helpfulness",
                "Builtin.Accuracy",
                math_evaluator.to_evaluator_reference()
            ],
            sampling_rate=0.5,
            description="Quality metrics for agent responses"
        )
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        config_name: str,
        runtime: RuntimeConstruct,
        evaluators: list[str],
        sampling_rate: float = 1.0,
        description: str | None = None,
        enable_on_create: bool = True,
    ) -> None:
        """Create an online evaluation configuration for a runtime.

        Args:
            scope: CDK construct scope
            id: Construct ID
            config_name: Name for the evaluation configuration
            runtime: AgentCore runtime to evaluate
            evaluators: List of evaluator IDs (built-in or custom)
            sampling_rate: Sampling rate (0.0-1.0) for evaluation
            description: Optional description of the evaluation purpose
            enable_on_create: Enable evaluation immediately upon creation

        Example:
            OnlineEvaluationConstruct(
                self, "SkillEvaluation",
                config_name="skill_metrics",
                runtime=skill_runtime,
                evaluators=["Builtin.Relevance", custom_eval.to_evaluator_reference()],
                sampling_rate=1.0
            )
        """
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)

        # Config names only allow letters, numbers, and underscores — use snake_case
        prefixed_config_name = to_snake_case(config_name)

        # Lambda execution role with permissions to create evaluation configs
        lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
            inline_policies={
                "EvaluationManagementPolicy": iam.PolicyDocument(
                    statements=[
                        # Permissions to manage online evaluation configs
                        iam.PolicyStatement(
                            actions=[
                                "bedrock-agentcore:CreateOnlineEvaluationConfig",
                                "bedrock-agentcore:GetOnlineEvaluationConfig",
                                "bedrock-agentcore:UpdateOnlineEvaluationConfig",
                                "bedrock-agentcore:DeleteOnlineEvaluationConfig",
                                "bedrock-agentcore:ListOnlineEvaluationConfigs",
                                "bedrock-agentcore:GetAgentRuntime",  # SDK validates agent exists
                            ],
                            resources=["*"],  # CDK role will be used when moved to L2 constructs
                        ),
                        # SDK needs permission to create IAM roles for evaluation execution
                        iam.PolicyStatement(
                            actions=[
                                "iam:GetRole",
                                "iam:CreateRole",
                                "iam:AttachRolePolicy",
                                "iam:PutRolePolicy",
                                "iam:PassRole",
                            ],
                            resources=["*"],  # CDK role will be used when moved to L2 constructs
                        ),
                        # SDK needs permission to configure CloudWatch Logs index policies
                        iam.PolicyStatement(
                            actions=[
                                "logs:DescribeLogGroups",
                                "logs:CreateLogGroup",
                                "logs:DescribeIndexPolicies",
                                "logs:PutIndexPolicy",
                            ],
                            resources=[
                                f"arn:aws:logs:{stack.region}:{stack.account}:log-group:aws/spans",
                                f"arn:aws:logs:{stack.region}:{stack.account}:log-group:aws/spans:*",
                            ],
                        ),
                    ]
                ),
            },
        )

        # Extract agent ID from runtime ARN for SDK
        # Runtime ARN format: arn:aws:bedrock-agentcore:region:account:runtime/agent_name-randomid
        agent_id = cdk.Fn.select(1, cdk.Fn.split("/", runtime.runtime.agent_runtime_arn))

        # Custom resource Lambda handler using AgentCore SDK
        handler = lambda_.Function(
            self,
            "Handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            role=lambda_role,
            timeout=cdk.Duration.minutes(2),
            code=lambda_.Code.from_inline(
                """
import json
from bedrock_agentcore_starter_toolkit import Evaluation

def handler(event, context):
    print(f"Event: {json.dumps(event)}")

    request_type = event['RequestType']
    props = event['ResourceProperties']

    config_name = props['ConfigName']
    agent_id = props['AgentId']
    evaluators = props['Evaluators']
    sampling_rate = float(props['SamplingRate'])
    description = props.get('Description', 'Online evaluation config')
    enable_on_create = props.get('EnableOnCreate', 'true').lower() == 'true'

    eval_client = Evaluation()

    try:
        if request_type == 'Create':
            response = eval_client.create_online_config(
                config_name=config_name,
                agent_id=agent_id,
                sampling_rate=sampling_rate,
                evaluator_list=evaluators,
                config_description=description,
                auto_create_execution_role=True,  # Let SDK create the execution role
                enable_on_create=enable_on_create
            )
            config_id = response['onlineEvaluationConfigId']

            return {
                'PhysicalResourceId': config_id,
                'Data': {
                    'ConfigId': config_id,
                    'ConfigArn': response.get('onlineEvaluationConfigArn', ''),
                    'Status': response.get('status', 'CREATED')
                }
            }

        elif request_type == 'Update':
            # For updates, delete old and create new
            old_config_id = event.get('PhysicalResourceId')

            if old_config_id and not old_config_id.startswith('PENDING'):
                try:
                    eval_client.delete_online_config(config_id=old_config_id)
                except Exception as e:
                    print(f"Failed to delete old config: {e}")

            response = eval_client.create_online_config(
                config_name=config_name,
                agent_id=agent_id,
                sampling_rate=sampling_rate,
                evaluator_list=evaluators,
                config_description=description,
                auto_create_execution_role=True,
                enable_on_create=enable_on_create
            )
            config_id = response['onlineEvaluationConfigId']

            return {
                'PhysicalResourceId': config_id,
                'Data': {
                    'ConfigId': config_id,
                    'ConfigArn': response.get('onlineEvaluationConfigArn', ''),
                    'Status': response.get('status', 'UPDATED')
                }
            }

        elif request_type == 'Delete':
            config_id = event.get('PhysicalResourceId')
            if config_id and not config_id.startswith('PENDING'):
                try:
                    eval_client.delete_online_config(config_id=config_id)
                except Exception as e:
                    print(f"Failed to delete config: {e}")

            return {
                'PhysicalResourceId': config_id or 'DELETED',
                'Data': {'Status': 'DELETED'}
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise
"""
            ),
        )

        # Add the AgentCore SDK layer
        sdk_layer = lambda_.LayerVersion(
            self,
            "AgentCoreSDKLayer",
            code=lambda_.Code.from_asset(
                "layers/agentcore_sdk",
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install bedrock-agentcore-starter-toolkit -t /asset-output/python --platform manylinux2014_x86_64 --implementation cp --python-version 3.13 --only-binary=:all: --upgrade",
                    ],
                ),
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
            description="AgentCore Starter Toolkit SDK",
        )
        handler.add_layers(sdk_layer)

        # Create custom resource provider
        provider = cr.Provider(
            self,
            "Provider",
            on_event_handler=handler,
        )

        # Create the custom resource
        resource = cdk.CustomResource(
            self,
            "Resource",
            service_token=provider.service_token,
            properties={
                "ConfigName": prefixed_config_name,
                "AgentId": agent_id,
                "Evaluators": evaluators,
                "SamplingRate": str(sampling_rate),
                "Description": description or f"Online evaluation for {config_name}",
                "EnableOnCreate": str(enable_on_create).lower(),
            },
        )

        self._config_id = resource.get_att_string("ConfigId")
        self._config_arn = resource.get_att_string("ConfigArn")
        self._status = resource.get_att_string("Status")

    @property
    def config_id(self) -> str:
        """The online evaluation configuration ID.

        Returns:
            Configuration ID for reference in API calls
        """
        return self._config_id

    @property
    def config_arn(self) -> str:
        """The full ARN of the online evaluation configuration.

        Returns:
            Full ARN string for the evaluation config
        """
        return self._config_arn

    @property
    def status(self) -> str:
        """The status of the evaluation configuration.

        Returns:
            Status string (e.g., "CREATED", "ENABLED", "DISABLED")
        """
        return self._status
