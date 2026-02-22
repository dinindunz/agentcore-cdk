import os

from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk.aws_bedrock_agentcore_alpha import ToolSchema
from constructs import Construct

from ..gateway import GatewayConstruct
from ...utils import to_pascal_case


class LambdaTargetConstruct(Construct):
    """Docker Lambda function registered as a gateway target with invoke permissions and dependency handling."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        asset_path: str,
        gateway: GatewayConstruct,
        target_name: str,
        description: str,
        environment: dict[str, str] | None = None,
    ) -> None:
        super().__init__(scope, id)

        # __file__ is src/cdk/constructs/gateway_targets/lambda_target.py — ../../.. resolves to src/
        asset_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", asset_path
        )

        self._function = lambda_.DockerImageFunction(
            self,
            "Function",
            architecture=lambda_.Architecture.ARM_64,
            code=lambda_.DockerImageCode.from_image_asset(
                asset_dir,
                platform=ecr_assets.Platform.LINUX_ARM64,
            ),
            environment=environment,
        )

        # Grant the gateway's service role permission to invoke this Lambda
        # (the L2 add_lambda_target does not auto-grant this)
        self._function.grant_invoke(gateway.gateway.role)

        # Register as a Lambda target on the gateway
        target = gateway.gateway.add_lambda_target(
            f"{to_pascal_case(target_name)}Target",
            gateway_target_name=target_name,
            description=description,
            lambda_function=self._function,
            tool_schema=ToolSchema.from_local_asset(
                os.path.join(asset_dir, "schema.json")
            ),
        )

        # Ensure the gateway's service role policy (with lambda:InvokeFunction) is created
        # before the target — AgentCore validates this at CreateGatewayTarget time
        if gateway.gateway.role.node.try_find_child("DefaultPolicy"):
            target.node.add_dependency(
                gateway.gateway.role.node.find_child("DefaultPolicy")
            )

    @property
    def function(self) -> lambda_.DockerImageFunction:
        return self._function
