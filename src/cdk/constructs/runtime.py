import os

import aws_cdk as cdk
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_bedrock_agentcore_alpha import (
    AgentRuntimeArtifact,
    Runtime,
    RuntimeAuthorizerConfiguration,
    ProtocolType,
)
from cdk_ecr_deployment import ECRDeployment, DockerImageName
from constructs import Construct

from .cognito import UserPoolConstruct
from ..utils import to_kebab_case, to_snake_case


class RuntimeConstruct(Construct):
    """AgentCore runtime with execution role, ECR repository, container artifact, and SSM ARN parameter."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        runtime_name: str,
        asset_path: str,
        protocol: ProtocolType,
        auth_pool: UserPoolConstruct,
        environment_variables: dict[str, str] | None = None,
    ) -> None:
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)

        ssm_prefix = f"/{stack_prefix}"
        # Derive SSM key from construct id: "AgentRuntime" -> "agent-runtime-arn"
        ssm_param_key = f"{to_kebab_case(id)}-arn"

        # Runtime names only allow letters, numbers, and underscores — use snake_case
        prefixed_runtime_name = (
            f"{to_snake_case(stack.stack_name)}_{to_snake_case(runtime_name)}"
        )

        self._role = iam.Role(
            self,
            "ExecutionRole",
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
                                f"arn:aws:ssm:{stack.region}:{stack.account}:parameter{ssm_prefix}/*"
                            ],
                        ),
                        iam.PolicyStatement(
                            actions=["secretsmanager:GetSecretValue"],
                            resources=[
                                f"arn:aws:secretsmanager:{stack.region}:{stack.account}:secret:{stack_prefix}/*"
                            ],
                        ),
                    ]
                ),
            },
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"),
            ],
        )

        # Create a named ECR repository for this runtime
        repo_name = f"{stack_prefix}-{to_kebab_case(runtime_name)}"
        self._ecr_repo = ecr.Repository(
            self,
            "EcrRepo",
            repository_name=repo_name,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            empty_on_delete=True,
            lifecycle_rules=[ecr.LifecycleRule(max_image_count=5)],
        )

        # Build the Docker image (pushed to CDK bootstrap ECR during synth/deploy)
        # __file__ is src/cdk/constructs/runtime.py — ../.. resolves to src/
        docker_asset = ecr_assets.DockerImageAsset(
            self,
            "DockerAsset",
            directory=os.path.join(os.path.dirname(__file__), "..", "..", asset_path),
        )

        # Copy the built image into our named ECR repository
        image_deployment = ECRDeployment(
            self,
            "ImageDeployment",
            src=DockerImageName(docker_asset.image_uri),
            dest=DockerImageName(
                f"{self._ecr_repo.repository_uri}:{docker_asset.image_tag}"
            ),
        )

        # Grant the runtime execution role permission to pull from our ECR repo
        self._ecr_repo.grant_pull(self._role)

        artifact = AgentRuntimeArtifact.from_ecr_repository(
            self._ecr_repo, docker_asset.image_tag
        )

        self._runtime = Runtime(
            self,
            "Runtime",
            runtime_name=prefixed_runtime_name,
            execution_role=self._role,
            agent_runtime_artifact=artifact,
            protocol_configuration=protocol,
            authorizer_configuration=RuntimeAuthorizerConfiguration.using_cognito(
                auth_pool.user_pool,
                [auth_pool.client],
            ),
            environment_variables=environment_variables,
        )

        # Ensure the image is copied into our ECR repo before the Runtime is created
        self._runtime.node.add_dependency(image_deployment)

        ssm.StringParameter(
            self,
            "ArnParam",
            parameter_name=f"{ssm_prefix}/{ssm_param_key}",
            string_value=self._runtime.agent_runtime_arn,
        )

    @property
    def runtime(self) -> Runtime:
        return self._runtime

    @property
    def role(self) -> iam.Role:
        return self._role

    @property
    def ecr_repository(self) -> ecr.Repository:
        return self._ecr_repo
