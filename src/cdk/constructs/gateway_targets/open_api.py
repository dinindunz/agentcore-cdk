import os
from collections.abc import Sequence

from aws_cdk.aws_bedrock_agentcore_alpha import ApiSchema, GatewayCredentialProvider
from constructs import Construct

from ...utils import to_pascal_case
from ..gateway import GatewayConstruct


class OpenApiTargetConstruct(Construct):
    """OpenAPI REST endpoint registered as a gateway target."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        gateway: GatewayConstruct,
        target_name: str,
        description: str,
        schema_path: str,
        credential_provider_configurations: (Sequence[GatewayCredentialProvider] | None) = None,
    ) -> None:
        super().__init__(scope, id)

        # __file__ is src/cdk/constructs/gateway_targets/open_api.py — ../../.. resolves to src/
        schema_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", schema_path)

        gateway.gateway.add_open_api_target(
            f"{to_pascal_case(target_name)}Target",
            gateway_target_name=target_name,
            description=description,
            api_schema=ApiSchema.from_local_asset(schema_file),
            credential_provider_configurations=credential_provider_configurations or [],
        )
