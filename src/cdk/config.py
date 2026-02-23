"""CDK configuration for AgentCore stacks."""

import os
from dataclasses import dataclass


@dataclass
class AgentCoreConfig:
    """Configuration for AgentCore CDK stacks."""

    enable_observability: bool
    region: str | None
    account: str | None

    @classmethod
    def from_env(cls) -> "AgentCoreConfig":
        """Load configuration from environment variables."""
        return cls(
            enable_observability=os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true",
            region=os.getenv("REGION_NAME"),
            account=os.getenv("AWS_ACCOUNT"),
        )


# Global config instance - initialized from environment
config = AgentCoreConfig.from_env()
