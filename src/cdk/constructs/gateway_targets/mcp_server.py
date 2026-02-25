from collections.abc import Sequence

from aws_cdk.aws_bedrock_agentcore_alpha import GatewayCredentialProvider
from constructs import Construct

from ...utils import to_pascal_case
from ..gateway import GatewayConstruct


class McpServerTargetConstruct(Construct):
    """MCP server runtime registered as a gateway target."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        gateway: GatewayConstruct,
        target_name: str,
        description: str,
        endpoint: str,
        credential_provider_configurations: (Sequence[GatewayCredentialProvider] | None) = None,
    ) -> None:
        super().__init__(scope, id)

        gateway.gateway.add_mcp_server_target(
            f"{to_pascal_case(target_name)}Target",
            gateway_target_name=target_name,
            description=description,
            endpoint=endpoint,
            credential_provider_configurations=credential_provider_configurations or [],
        )
