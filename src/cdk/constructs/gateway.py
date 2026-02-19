import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_bedrock_agentcore_alpha import Gateway, GatewayAuthorizer
from constructs import Construct

from ..utils import to_kebab_case


class GatewayConstruct(Construct):
    """AgentCore gateway with OAuth service role permissions and SSM URL parameter."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        gateway_name: str,
        authorizer_configuration: GatewayAuthorizer,
        credential_provider_name: str,
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

        # Service role permissions for the OAuth credential provider flow
        workload_identity_base = f"arn:aws:bedrock-agentcore:{stack.region}:{stack.account}:workload-identity-directory/default"
        token_vault_base = f"arn:aws:bedrock-agentcore:{stack.region}:{stack.account}:token-vault/default"
        self._gateway.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:CompleteResourceTokenAuth",
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetResourceOauth2Token",
                ],
                resources=[
                    workload_identity_base,
                    f"{workload_identity_base}/workload-identity/{prefixed_gateway_name}-*",
                    token_vault_base,
                    f"{token_vault_base}/oauth2credentialprovider/{credential_provider_name}",
                ],
            )
        )

        ssm.StringParameter(
            self,
            "UrlParam",
            parameter_name=self._ssm_url_param_name,
            string_value=f"https://{self._gateway.gateway_id}.gateway.bedrock-agentcore.{stack.region}.amazonaws.com/mcp",
        )

    @property
    def gateway(self) -> Gateway:
        return self._gateway

    @property
    def ssm_url_param_name(self) -> str:
        return self._ssm_url_param_name
