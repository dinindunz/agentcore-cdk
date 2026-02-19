from typing import Sequence

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_bedrock_agentcore_alpha import Gateway, GatewayAuthorizer
from constructs import Construct

from ..utils import to_kebab_case


class GatewayConstruct(Construct):
    """AgentCore gateway with credential provider service role permissions and SSM URL parameter."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        gateway_name: str,
        authorizer_configuration: GatewayAuthorizer,
        oauth2_provider_names: Sequence[str] | None = None,
        api_key_provider_names: Sequence[str] | None = None,
    ) -> None:
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)
        gateway_name_kebab = to_kebab_case(gateway_name)

        ssm_prefix = f"/{stack_prefix}"
        ssm_param_key = f"{gateway_name_kebab}-url"
        prefixed_gateway_name = f"{stack_prefix}-{gateway_name_kebab}"
        self._ssm_url_param_name = f"{ssm_prefix}/{ssm_param_key}"

        self._gateway = Gateway(
            self,
            "Gateway",
            gateway_name=prefixed_gateway_name,
            authorizer_configuration=authorizer_configuration,
        )

        # Service role permissions for credential provider flows
        has_oauth2 = bool(oauth2_provider_names)
        has_api_key = bool(api_key_provider_names)

        if has_oauth2 or has_api_key:
            workload_identity_base = f"arn:aws:bedrock-agentcore:{stack.region}:{stack.account}:workload-identity-directory/default"
            token_vault_base = f"arn:aws:bedrock-agentcore:{stack.region}:{stack.account}:token-vault/default"

            actions = [
                "bedrock-agentcore:CompleteResourceTokenAuth",
                "bedrock-agentcore:GetWorkloadAccessToken",
            ]
            resources = [
                workload_identity_base,
                f"{workload_identity_base}/workload-identity/{prefixed_gateway_name}-*",
                token_vault_base,
            ]

            if has_oauth2:
                actions.append("bedrock-agentcore:GetResourceOauth2Token")
                for name in oauth2_provider_names:
                    resources.append(
                        f"{token_vault_base}/oauth2credentialprovider/{name}"
                    )

            if has_api_key:
                actions.append("bedrock-agentcore:GetResourceApiKeyToken")
                for name in api_key_provider_names:
                    resources.append(
                        f"{token_vault_base}/apikeycredentialprovider/{name}"
                    )

            self._gateway.role.add_to_policy(
                iam.PolicyStatement(actions=actions, resources=resources)
            )

        self._url = f"https://{self._gateway.gateway_id}.gateway.bedrock-agentcore.{stack.region}.amazonaws.com/mcp"

        ssm.StringParameter(
            self,
            "UrlParam",
            parameter_name=self._ssm_url_param_name,
            string_value=self._url,
        )

    @property
    def gateway(self) -> Gateway:
        return self._gateway

    @property
    def url(self) -> str:
        return self._url

    @property
    def ssm_url_param_name(self) -> str:
        return self._ssm_url_param_name
