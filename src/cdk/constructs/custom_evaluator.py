import json
from typing import Literal

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import custom_resources as cr
from constructs import Construct

from ..utils import to_snake_case


class ScoringSchemaDefinition:
    """Defines the scoring schema for a custom evaluator.

    Supports both numbered scales and binary (Yes/No) schemas.
    """

    @staticmethod
    def numbered_scale(
        min_value: int,
        max_value: int,
        description: str | None = None,
    ) -> dict:
        """Create a numbered scale scoring schema.

        Args:
            min_value: Minimum score value (e.g., 1)
            max_value: Maximum score value (e.g., 5)
            description: Optional description of what the scale measures (not used - provided for API consistency)

        Returns:
            Scoring schema dictionary for AgentCore API

        Example:
            # 5-point scale for helpfulness
            ScoringSchemaDefinition.numbered_scale(
                min_value=1,
                max_value=5
            )
        """
        # AgentCore SDK expects 'numerical' to be a list with each score value as a dict
        # Each dict must have: value (int), label (str), definition (str)
        return {
            "numerical": [
                {"value": i, "label": str(i), "definition": f"Score {i}"}
                for i in range(min_value, max_value + 1)
            ]
        }

    @staticmethod
    def binary(description: str | None = None) -> dict:
        """Create a binary (Yes/No) scoring schema.

        Args:
            description: Optional description of what Yes/No represents (not used - provided for API consistency)

        Returns:
            Scoring schema dictionary for AgentCore API

        Example:
            # Binary for factual accuracy
            ScoringSchemaDefinition.binary()
        """
        # AgentCore SDK expects 'categorical' to be a list of option dicts
        # Each option must have 'label' and 'definition' fields
        return {
            "categorical": [
                {"label": "Yes", "definition": "Criteria is met"},
                {"label": "No", "definition": "Criteria is not met"},
            ]
        }


class ModelConfiguration:
    """Model inference configuration for custom evaluators."""

    def __init__(
        self,
        model_id: str,
        *,
        temperature: float = 0.0,
        top_p: float = 0.9,
        max_tokens: int = 2048,
        stop_sequences: list[str] | None = None,
    ) -> None:
        """Configure the LLM model for evaluation.

        Args:
            model_id: Bedrock model ID (e.g., "anthropic.claude-opus-4-6-v1:0")
            temperature: Sampling temperature (0.0-1.0). Lower = more deterministic
            top_p: Nucleus sampling threshold (0.0-1.0)
            max_tokens: Maximum output tokens for evaluation response
            stop_sequences: Optional list of stop sequences

        Example:
            ModelConfiguration(
                model_id="anthropic.claude-sonnet-4-5-v3:0",
                temperature=0.0,  # Deterministic for consistent evaluation
                top_p=0.95,
                max_tokens=1024
            )
        """
        self.model_id = model_id
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stop_sequences = stop_sequences or []

    def to_dict(self) -> dict:
        """Convert to AgentCore API format with bedrockEvaluatorModelConfig wrapper."""
        inference_config = {
            "temperature": self.temperature,
            "topP": self.top_p,
            "maxTokens": self.max_tokens,
        }
        if self.stop_sequences:
            inference_config["stopSequences"] = self.stop_sequences

        # AgentCore SDK requires bedrockEvaluatorModelConfig wrapper with inferenceConfig
        return {
            "bedrockEvaluatorModelConfig": {
                "modelId": self.model_id,
                "inferenceConfig": inference_config,
            }
        }


# Type aliases for better IDE support
EvaluationLevel = Literal["session", "trace", "toolCall"]


# TODO: Refactor to use L2 constructs once they are available.
class CustomEvaluatorConstruct(Construct):
    """Creates an AgentCore custom evaluator.

    Uses the AgentCore SDK (bedrock-agentcore-starter-toolkit) in a Lambda-backed
    custom resource to create and manage custom evaluators. Custom evaluators allow
    you to define domain-specific evaluation logic using your choice of model, custom
    prompts, and scoring schemas. They can evaluate at session, trace, or tool call levels.

    Example:
        # Math accuracy evaluator for calculator operations
        math_eval = CustomEvaluatorConstruct(
            self, "MathAccuracyEvaluator",
            evaluator_name="MathAccuracy",
            evaluation_level="toolCall",
            prompt='''You are evaluating calculator tool calls for mathematical accuracy.

            Examine the tool input and output. Verify:
            1. The calculation is mathematically correct
            2. Precision is appropriate (no rounding errors)
            3. Units are handled correctly

            Score:
            5 = Perfect accuracy
            4 = Minor precision issues (e.g., 3.33 vs 3.333)
            3 = Correct approach but calculation error
            2 = Wrong operation used
            1 = Completely incorrect
            ''',
            scoring_schema=ScoringSchemaDefinition.numbered_scale(1, 5),
            model_config=ModelConfiguration(
                model_id="anthropic.claude-sonnet-4-5-v3:0",
                temperature=0.0  # Deterministic for consistency
            ),
            description="Validates mathematical correctness of calculator operations"
        )
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        evaluator_name: str,
        evaluation_level: EvaluationLevel,
        prompt: str,
        scoring_schema: dict,
        model_config: ModelConfiguration,
        description: str | None = None,
    ) -> None:
        """Create a custom evaluator.

        Args:
            scope: CDK construct scope
            id: Construct ID
            evaluator_name: Name for the evaluator (will be converted to snake_case)
            evaluation_level: Level to evaluate at ("session", "trace", or "toolCall")
            prompt: Custom evaluation instructions/prompt for the judge LLM
            scoring_schema: Scoring schema (use ScoringSchemaDefinition helper)
            model_config: Model configuration (use ModelConfiguration)
            description: Optional description of what this evaluator measures

        Example:
            CustomEvaluatorConstruct(
                self, "SkillWorkflowEvaluator",
                evaluator_name="SkillWorkflow",
                evaluation_level="trace",
                prompt="Evaluate if the agent completed all steps in the skill definition...",
                scoring_schema=ScoringSchemaDefinition.numbered_scale(1, 5),
                model_config=ModelConfiguration("anthropic.claude-opus-4-6-v1:0"),
                description="Validates skill execution completeness"
            )
        """
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)

        # Evaluator names must be snake_case
        sanitized_name = to_snake_case(evaluator_name)

        # Lambda execution role with permissions to create evaluators
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
                "EvaluatorManagementPolicy": iam.PolicyDocument(
                    statements=[
                        # Permissions to manage custom evaluators
                        iam.PolicyStatement(
                            actions=[
                                "bedrock-agentcore:CreateEvaluator",
                                "bedrock-agentcore:GetEvaluator",
                                "bedrock-agentcore:UpdateEvaluator",
                                "bedrock-agentcore:DeleteEvaluator",
                                "bedrock-agentcore:ListEvaluators",
                            ],
                            resources=["*"],
                        ),
                        # Permission to invoke Bedrock models for evaluation
                        iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream",
                            ],
                            resources=[f"arn:aws:bedrock:{stack.region}::foundation-model/*"],
                        ),
                    ]
                ),
            },
        )

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

    evaluator_name = props['EvaluatorName']
    evaluation_level = props['EvaluationLevel']
    prompt = props['Prompt']
    scoring_schema = json.loads(props['ScoringSchema'])
    model_config = json.loads(props['ModelConfig'])
    description = props.get('Description', '')

    # Convert evaluation level to uppercase for SDK (e.g., toolCall -> TOOL_CALL)
    # SDK expects: TRACE, TOOL_CALL, SESSION
    level_mapping = {
        'session': 'SESSION',
        'trace': 'TRACE',
        'toolCall': 'TOOL_CALL'
    }
    sdk_level = level_mapping.get(evaluation_level, evaluation_level.upper())

    # Build evaluator config for SDK
    evaluator_config = {
        'llmAsAJudge': {
            'instructions': prompt,
            'ratingScale': scoring_schema,
            'modelConfig': model_config
        }
    }

    eval_client = Evaluation()

    try:
        if request_type == 'Create':
            response = eval_client.create_evaluator(
                name=evaluator_name,
                level=sdk_level,
                description=description,
                config=evaluator_config
            )

            evaluator_id = response['evaluatorId']
            evaluator_arn = response['evaluatorArn']

            return {
                'PhysicalResourceId': evaluator_id,
                'Data': {
                    'EvaluatorId': evaluator_id,
                    'EvaluatorArn': evaluator_arn,
                    'EvaluatorName': evaluator_name
                }
            }

        elif request_type == 'Update':
            # For updates, delete old and create new
            old_evaluator_id = event.get('PhysicalResourceId')

            if old_evaluator_id and not old_evaluator_id.startswith('PENDING'):
                try:
                    eval_client.delete_evaluator(evaluator_id=old_evaluator_id)
                except Exception as e:
                    print(f"Failed to delete old evaluator: {e}")

            response = eval_client.create_evaluator(
                name=evaluator_name,
                level=sdk_level,
                description=description,
                config=evaluator_config
            )

            evaluator_id = response['evaluatorId']
            evaluator_arn = response['evaluatorArn']

            return {
                'PhysicalResourceId': evaluator_id,
                'Data': {
                    'EvaluatorId': evaluator_id,
                    'EvaluatorArn': evaluator_arn,
                    'EvaluatorName': evaluator_name
                }
            }

        elif request_type == 'Delete':
            evaluator_id = event.get('PhysicalResourceId')
            if evaluator_id and not evaluator_id.startswith('PENDING'):
                try:
                    eval_client.delete_evaluator(evaluator_id=evaluator_id)
                except Exception as e:
                    print(f"Failed to delete evaluator: {e}")

            return {
                'PhysicalResourceId': evaluator_id or 'DELETED',
                'Data': {'Status': 'DELETED'}
            }

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
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
                "EvaluatorName": sanitized_name,
                "EvaluationLevel": evaluation_level,
                "Prompt": prompt,
                "ScoringSchema": cdk.Fn.sub(json.dumps(scoring_schema)),
                "ModelConfig": cdk.Fn.sub(json.dumps(model_config.to_dict())),
                "Description": description or f"Custom evaluator: {evaluator_name}",
            },
        )

        self._evaluator_id = resource.get_att_string("EvaluatorId")
        self._evaluator_arn = resource.get_att_string("EvaluatorArn")
        self._evaluator_name = resource.get_att_string("EvaluatorName")

    @property
    def evaluator_id(self) -> str:
        """The evaluator ID (can be used in evaluation configs)."""
        return self._evaluator_id

    @property
    def evaluator_arn(self) -> str:
        """The full ARN of the evaluator."""
        return self._evaluator_arn

    @property
    def evaluator_name(self) -> str:
        """The evaluator name."""
        return self._evaluator_name

    def to_evaluator_reference(self) -> str:
        """Get the reference string for use in evaluation configs.

        Returns:
            Evaluator ID string that can be passed to OnlineEvaluationConstruct.evaluators

        Example:
            evaluators=[
                "Builtin.Helpfulness",
                math_eval.to_evaluator_reference(),  # Custom evaluator ID
            ]
        """
        return self.evaluator_id
