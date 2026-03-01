import aws_cdk as cdk
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

from ..utils import to_kebab_case


class UserPoolConstruct(Construct):
    """Cognito user pool with domain, resource server, client, and credentials secret.

    Resource names are automatically prefixed with the kebab-case stack name.
    The ``name`` param is a short identifier (e.g. ``"agent"``, ``"gateway"``, ``"mcp"``).

    Example:
        agent_pool = UserPoolConstruct(
            self, "AgentPool",
            name="agent",
            scope_description="Invoke agent runtime",
            access_token_validity=cdk.Duration.hours(1)
        )
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        name: str,
        scope_description: str,
        access_token_validity: cdk.Duration | None = None,
    ) -> None:
        """Create a Cognito user pool with domain and OAuth client.

        Args:
            scope: CDK construct scope
            id: Construct ID
            name: Short identifier (e.g., "agent", "gateway")
            scope_description: Description for the OAuth invoke scope
            access_token_validity: Access token expiry duration (default: 1 hour).
                Must be between 5 minutes and 24 hours for OAuth2 flows.

        Example:
            UserPoolConstruct(
                self, "GatewayPool",
                name="gateway",
                scope_description="Invoke gateway endpoints",
                access_token_validity=cdk.Duration.hours(1)
            )
        """
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)
        name_kebab = to_kebab_case(name)

        pool_name = f"{stack_prefix}-{name_kebab}-user-pool"
        domain_prefix = f"{stack_prefix}-{name_kebab}"
        resource_server_id = f"{name_kebab}"
        self._secret_name = f"{stack_prefix}/{name_kebab}-cognito"

        invoke_scope = cognito.ResourceServerScope(
            scope_name="invoke", scope_description=scope_description
        )

        self._user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=pool_name,
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self._domain = self._user_pool.add_domain(
            "Domain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix),
        )

        resource_server = self._user_pool.add_resource_server(
            "ResourceServer",
            identifier=resource_server_id,
            scopes=[invoke_scope],
        )

        self._client = self._user_pool.add_client(
            "Client",
            generate_secret=True,
            access_token_validity=access_token_validity or cdk.Duration.hours(1),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(client_credentials=True),
                scopes=[cognito.OAuthScope.resource_server(resource_server, invoke_scope)],
            ),
        )

        secretsmanager.Secret(
            self,
            "Secret",
            secret_name=self._secret_name,
            secret_object_value={
                "client_id": cdk.SecretValue.unsafe_plain_text(self._client.user_pool_client_id),
                "client_secret": self._client.user_pool_client_secret,
                "user_pool_id": cdk.SecretValue.unsafe_plain_text(self._user_pool.user_pool_id),
                "token_endpoint": cdk.SecretValue.unsafe_plain_text(
                    f"{self._domain.base_url()}/oauth2/token"
                ),
            },
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

    @property
    def user_pool(self) -> cognito.UserPool:
        """The Cognito user pool.

        Returns:
            The UserPool resource
        """
        return self._user_pool

    @property
    def domain(self) -> cognito.UserPoolDomain:
        """The Cognito domain for OAuth flows.

        Returns:
            The UserPoolDomain resource
        """
        return self._domain

    @property
    def client(self) -> cognito.UserPoolClient:
        """The Cognito user pool client.

        Returns:
            The UserPoolClient resource
        """
        return self._client

    @property
    def secret_name(self) -> str:
        """Secrets Manager secret name containing credentials.

        Returns:
            Secret name in format: {stack-prefix}/{name}-cognito
        """
        return self._secret_name
