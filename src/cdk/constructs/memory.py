import aws_cdk as cdk
from aws_cdk import aws_iam as iam, custom_resources as cr
from constructs import Construct

from ..utils import to_snake_case


# TODO: Refactor to use L2 constructs once they are available.
class MemoryConstruct(Construct):
    """AgentCore Memory with configurable strategies."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        memory_name: str,
        event_expiry_days: int = 90,
        enable_summary_strategy: bool = True,
        enable_preference_strategy: bool = True,
        enable_semantic_strategy: bool = False,
        enable_episodic_strategy: bool = False,
    ) -> None:
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)

        # Memory names only allow letters, numbers, and underscores — use snake_case
        prefixed_memory_name = (
            f"{to_snake_case(stack.stack_name)}_{to_snake_case(memory_name)}"
        )

        # Build memory strategies based on flags
        strategies = []

        if enable_summary_strategy:
            strategies.append(
                {
                    "summaryMemoryStrategy": {
                        "name": "SessionSummarizer",
                        "namespaces": [
                            "/strategies/summaries/actors/{actorId}/sessions/{sessionId}/"
                        ],
                    }
                }
            )

        if enable_preference_strategy:
            strategies.append(
                {
                    "userPreferenceMemoryStrategy": {
                        "name": "PreferenceLearner",
                        "namespaces": ["/strategies/preferences/actors/{actorId}/"],
                    }
                }
            )

        if enable_semantic_strategy:
            strategies.append(
                {
                    "semanticMemoryStrategy": {
                        "name": "FactExtractor",
                        "namespaces": ["/strategies/semantic/actors/{actorId}/"],
                    }
                }
            )

        if enable_episodic_strategy:
            strategies.append(
                {
                    "episodicMemoryStrategy": {
                        "name": "EpisodeTracker",
                        "namespaces": [
                            "/strategies/episodic/actors/{actorId}/sessions/{sessionId}/"
                        ],
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
                        resources=[
                            "*"
                        ],  # CDK role will be used when moved to L2 constructs
                    )
                ]
            ),
        )

        self._memory_id = self._memory.get_response_field("memory.id")

    @property
    def memory_id(self) -> str:
        """Memory resource ID for use in runtime environment variables."""
        return self._memory_id
