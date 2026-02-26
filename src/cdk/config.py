"""
Configuration loader for AgentCore CDK stack.

Loads environment-specific configuration from YAML files in config/ directory.
Provides type-safe configuration objects using Python dataclasses.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class MemoryStrategyConfig:
    """Memory strategy enablement flags."""

    summary: bool = True
    preference: bool = True
    semantic: bool = True
    # episodic: bool = False  # Currently disabled due to AgentCore namespace validation


@dataclass
class MemoryConfig:
    """AgentCore Memory configuration."""

    enabled: bool = False
    event_expiry_days: int = 90  # Valid range: 7-365
    strategies: MemoryStrategyConfig | None = None
    # Retrieval configuration for long-term memory strategies
    preference_top_k: int = 10
    preference_relevance_score: float = 0.2
    semantic_top_k: int = 10
    semantic_relevance_score: float = 0.2

    def __post_init__(self):
        """Validate and initialise nested dataclasses."""
        if self.strategies is None:
            self.strategies = MemoryStrategyConfig()
        elif isinstance(self.strategies, dict):
            self.strategies = MemoryStrategyConfig(**self.strategies)

        # Validate event_expiry_days range
        if not 7 <= self.event_expiry_days <= 365:
            raise ValueError(
                f"event_expiry_days must be between 7 and 365, got {self.event_expiry_days}"
            )

        # Validate retrieval config values
        if self.preference_top_k < 1:
            raise ValueError(f"preference_top_k must be >= 1, got {self.preference_top_k}")
        if not 0.0 <= self.preference_relevance_score <= 1.0:
            raise ValueError(
                f"preference_relevance_score must be between 0.0 and 1.0, got {self.preference_relevance_score}"
            )
        if self.semantic_top_k < 1:
            raise ValueError(f"semantic_top_k must be >= 1, got {self.semantic_top_k}")
        if not 0.0 <= self.semantic_relevance_score <= 1.0:
            raise ValueError(
                f"semantic_relevance_score must be between 0.0 and 1.0, got {self.semantic_relevance_score}"
            )


@dataclass
class AgentRuntimeConfig:
    """Agent runtime configuration."""

    log_level: str = "INFO"
    otel_logging_enabled: bool = False
    model_temperature: float = 0.7
    model_max_tokens: int = 4096

    def __post_init__(self):
        """Validate log level and model parameters."""
        self._validate_log_level(self.log_level)
        self.log_level = self.log_level.upper()

        # Validate temperature (0.0 to 1.0)
        if not 0.0 <= self.model_temperature <= 1.0:
            raise ValueError(
                f"model_temperature must be between 0.0 and 1.0, got {self.model_temperature}"
            )

        # Validate max_tokens (must be positive)
        if self.model_max_tokens < 1:
            raise ValueError(f"model_max_tokens must be >= 1, got {self.model_max_tokens}")

    @staticmethod
    def _validate_log_level(level: str) -> None:
        """Validate log level value."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if level.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {level}")


@dataclass
class McpServerConfig:
    """MCP server runtime configuration."""

    log_level: str = "INFO"

    def __post_init__(self):
        """Validate log level."""
        AgentRuntimeConfig._validate_log_level(self.log_level)
        self.log_level = self.log_level.upper()


@dataclass
class LambdaTargetConfig:
    """Lambda target configuration."""

    log_level: str = "INFO"

    def __post_init__(self):
        """Validate log level."""
        AgentRuntimeConfig._validate_log_level(self.log_level)
        self.log_level = self.log_level.upper()


@dataclass
class LambdaTargetsConfig:
    """Lambda targets configuration."""

    skill_search: LambdaTargetConfig | None = None
    temperature_converter: LambdaTargetConfig | None = None

    def __post_init__(self):
        """Initialise nested dataclasses from dicts."""
        if self.skill_search is None:
            self.skill_search = LambdaTargetConfig()
        elif isinstance(self.skill_search, dict):
            self.skill_search = LambdaTargetConfig(**self.skill_search)

        if self.temperature_converter is None:
            self.temperature_converter = LambdaTargetConfig()
        elif isinstance(self.temperature_converter, dict):
            self.temperature_converter = LambdaTargetConfig(**self.temperature_converter)


@dataclass
class McpRuntimesConfig:
    """MCP runtimes configuration (AgentCore Runtime constructs)."""

    calculator: McpServerConfig | None = None

    def __post_init__(self):
        """Initialise nested dataclasses from dicts."""
        if self.calculator is None:
            self.calculator = McpServerConfig()
        elif isinstance(self.calculator, dict):
            self.calculator = McpServerConfig(**self.calculator)


@dataclass
class ObservabilityConfig:
    """Phoenix observability configuration."""

    enabled: bool = False  # Enable Phoenix tracing


@dataclass
class EvaluationConfig:
    """AgentCore online evaluation configuration."""

    sampling_rate: float = 100.0  # 0.0 to 100.0 (percentage of interactions to evaluate)
    enable_on_create: bool = True  # Enable evaluation config immediately after creation

    def __post_init__(self):
        """Validate sampling rate."""
        if not 0.0 <= self.sampling_rate <= 100.0:
            raise ValueError(
                f"sampling_rate must be between 0.0 and 100.0, got {self.sampling_rate}"
            )


@dataclass
class InferenceProfileConfig:
    """Bedrock inference profile configuration for cost tracking."""

    model_id: str = (
        "au.anthropic.claude-sonnet-4-6"  # Cross-region inference profile ID or foundation model ID
    )
    description: str = ""  # Profile description
    tags: dict[str, str] | None = None  # Cost allocation tags

    def __post_init__(self):
        """Validate inference profile configuration."""
        if not self.model_id:
            raise ValueError("model_id is required for inference_profile")

        # Initialise tags as empty dict if None
        if self.tags is None:
            self.tags = {}


@dataclass
class AgentCoreConfig:
    """Complete AgentCore stack configuration."""

    environment: str  # dev, test, prod
    memory: MemoryConfig
    agent_runtime: AgentRuntimeConfig
    mcp_runtimes: McpRuntimesConfig
    lambda_targets: LambdaTargetsConfig
    observability: ObservabilityConfig
    evaluation: EvaluationConfig
    inference_profile: InferenceProfileConfig | None = None

    def __post_init__(self):
        """Initialise nested dataclasses from dicts."""
        if isinstance(self.memory, dict):
            self.memory = MemoryConfig(**self.memory)
        if isinstance(self.agent_runtime, dict):
            self.agent_runtime = AgentRuntimeConfig(**self.agent_runtime)
        if isinstance(self.mcp_runtimes, dict):
            self.mcp_runtimes = McpRuntimesConfig(**self.mcp_runtimes)
        if isinstance(self.lambda_targets, dict):
            self.lambda_targets = LambdaTargetsConfig(**self.lambda_targets)
        if isinstance(self.observability, dict):
            self.observability = ObservabilityConfig(**self.observability)
        if isinstance(self.evaluation, dict):
            self.evaluation = EvaluationConfig(**self.evaluation)
        if self.inference_profile is None:
            self.inference_profile = InferenceProfileConfig()
        elif isinstance(self.inference_profile, dict):
            self.inference_profile = InferenceProfileConfig(**self.inference_profile)


def load_config(environment: str) -> AgentCoreConfig:
    """
    Load environment-specific configuration from YAML file.

    Args:
        environment: Environment name (dev, test, prod)

    Returns:
        AgentCoreConfig instance with validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    # Determine config file path (relative to project root)
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / "config" / f"{environment}.yaml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}\n"
            f"Available configs: {list((project_root / 'config').glob('*.yaml'))}"
        )

    # Load YAML configuration
    with open(config_file) as f:
        config_data = yaml.safe_load(f)

    # Add environment to config data
    config_data["environment"] = environment

    # Create and validate config object
    return AgentCoreConfig(**config_data)


def get_config_from_context(app: Any) -> AgentCoreConfig:
    """
    Helper to load configuration from CDK app context.

    Usage in app.py:
        config = get_config_from_context(app)

    Args:
        app: CDK App instance

    Returns:
        AgentCoreConfig instance
    """
    env = app.node.try_get_context("env")
    if not env:
        raise ValueError("Environment not specified. Use: cdk deploy --context env=dev")
    return load_config(env)
