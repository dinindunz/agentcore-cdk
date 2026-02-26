import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm
from aws_cdk import custom_resources as cr
from constructs import Construct

from ..utils import to_kebab_case, to_snake_case

# Default namespace patterns
DEFAULT_SUMMARY_NAMESPACES = ["/summaries/{actorId}/{sessionId}/"]
DEFAULT_PREFERENCE_NAMESPACES = ["/preferences/{actorId}/"]
DEFAULT_SEMANTIC_NAMESPACES = ["/facts/{actorId}/"]
DEFAULT_EPISODIC_NAMESPACES = ["/episodes/{actorId}/{sessionId}/"]


# TODO: Refactor to use L2 constructs once they are available.
class MemoryConstruct(Construct):
    """AgentCore Memory with configurable strategies.

    Example:
        memory = MemoryConstruct(
            self, "Memory",
            memory_name="agent",
            event_expiry_days=90,
            enable_summary_strategy=True,
            enable_preference_strategy=True
        )
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        memory_name: str,
        event_expiry_days: int = 90,
        enable_summary_strategy: bool = True,
        enable_preference_strategy: bool = True,
        enable_semantic_strategy: bool = True,
        enable_episodic_strategy: bool = False,  # TODO: Disabled - Fix configuration issues
        summary_namespaces: list[str] | None = None,
        preference_namespaces: list[str] | None = None,
        semantic_namespaces: list[str] | None = None,
        episodic_namespaces: list[str] | None = None,
    ) -> None:
        """Create an AgentCore memory with configurable strategies.

        Args:
            scope: CDK construct scope
            id: Construct ID
            memory_name: Name for the memory (will be prefixed with stack name)
            event_expiry_days: Days to retain memory events (7-365)
            enable_summary_strategy: Enable session summarisation
            enable_preference_strategy: Enable user preference learning
            enable_semantic_strategy: Enable fact extraction
            enable_episodic_strategy: Enable episode tracking
            summary_namespaces: Custom namespaces for summary strategy (default: DEFAULT_SUMMARY_NAMESPACES)
            preference_namespaces: Custom namespaces for preference strategy (default: DEFAULT_PREFERENCE_NAMESPACES)
            semantic_namespaces: Custom namespaces for semantic strategy (default: DEFAULT_SEMANTIC_NAMESPACES)
            episodic_namespaces: Custom namespaces for episodic strategy (default: DEFAULT_EPISODIC_NAMESPACES)

        Example:
            MemoryConstruct(
                self, "Memory",
                memory_name="agent_memory",
                event_expiry_days=90,
                enable_summary_strategy=True,
                enable_preference_strategy=True,
                # Optional: override default namespaces
                preference_namespaces=["/custom/prefs/{actorId}/"]
            )
        """
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)

        # Memory names only allow letters, numbers, and underscores — use snake_case
        prefixed_memory_name = f"{to_snake_case(stack.stack_name)}_{to_snake_case(memory_name)}"

        # Build memory strategies based on flags
        strategies = []

        if enable_summary_strategy:
            strategies.append(
                {
                    "summaryMemoryStrategy": {
                        "name": "SessionSummarizer",
                        "namespaces": summary_namespaces or DEFAULT_SUMMARY_NAMESPACES,
                    }
                }
            )

        if enable_preference_strategy:
            strategies.append(
                {
                    "userPreferenceMemoryStrategy": {
                        "name": "PreferenceLearner",
                        "namespaces": preference_namespaces or DEFAULT_PREFERENCE_NAMESPACES,
                    }
                }
            )

        if enable_semantic_strategy:
            strategies.append(
                {
                    "semanticMemoryStrategy": {
                        "name": "FactExtractor",
                        "namespaces": semantic_namespaces or DEFAULT_SEMANTIC_NAMESPACES,
                    }
                }
            )

        if enable_episodic_strategy:
            strategies.append(
                {
                    "episodicMemoryStrategy": {
                        "name": "EpisodeTracker",
                        "namespaces": episodic_namespaces or DEFAULT_EPISODIC_NAMESPACES,
                    }
                }
            )

        # Create memory resource
        # Note: We omit on_update to force replacement when properties change.
        # updateMemory has a different memoryStrategies structure (addMemoryStrategies,
        # modifyMemoryStrategies, deleteMemoryStrategies) which would require complex
        # diff logic. Replacement is simpler for strategy changes.
        self._memory = cr.AwsCustomResource(
            self,
            "Memory",
            on_create=cr.AwsSdkCall(
                service="bedrock-agentcore-control",
                action="createMemory",
                parameters={
                    "name": prefixed_memory_name,
                    "description": f"Memory for {memory_name}",
                    "eventExpiryDuration": event_expiry_days,
                    "memoryStrategies": strategies if strategies else None,
                },
                physical_resource_id=cr.PhysicalResourceId.from_response("memory.id"),
            ),
            on_delete=cr.AwsSdkCall(
                service="bedrock-agentcore-control",
                action="deleteMemory",
                parameters={
                    "memoryId": cr.PhysicalResourceIdReference(),
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=[
                            "bedrock-agentcore:CreateMemory",
                            "bedrock-agentcore:DeleteMemory",
                            "bedrock-agentcore:GetMemory",
                        ],
                        resources=["*"],  # CDK role will be used when moved to L2 constructs
                    )
                ]
            ),
        )

        self._memory_id = self._memory.get_response_field("memory.id")

        # Export memory ID to SSM for easy script access (matches gateway naming convention)
        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)
        ssm_prefix = f"/{stack_prefix}"
        ssm.StringParameter(
            self,
            "MemoryIdParam",
            parameter_name=f"{ssm_prefix}/memory-id",
            string_value=self._memory_id,
            description="AgentCore Memory ID for agent memory strategies",
        )

    @property
    def memory_id(self) -> str:
        """Memory resource ID for use in runtime environment variables.

        Returns:
            Memory ID string that can be passed to runtime containers
        """
        return self._memory_id
