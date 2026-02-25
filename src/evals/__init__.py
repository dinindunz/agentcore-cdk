"""Custom evaluator definitions for AgentCore agent.

This package contains evaluator configurations for domain-specific validation
of GitHub analysis skills. Each module defines:
- Evaluator name and level
- Model configuration (ID, temperature, tokens)
- Scoring schema (numbered scale or binary)
- Evaluation prompt

Import these in your CDK stack to create custom evaluators.
"""

from . import (
    math_accuracy,
    temperature_conversion,
    skill_workflow,
    github_integrity,
    output_format,
)

__all__ = [
    "math_accuracy",
    "temperature_conversion",
    "skill_workflow",
    "github_integrity",
    "output_format",
]

# Evaluator registry for easy iteration
EVALUATORS = {
    "math_accuracy": math_accuracy,
    "temperature_conversion": temperature_conversion,
    "skill_workflow": skill_workflow,
    "github_integrity": github_integrity,
    "output_format": output_format,
}
