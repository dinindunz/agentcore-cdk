import re


def to_kebab_case(s: str) -> str:
    """Convert PascalCase, camelCase, or snake_case to kebab-case.

    Examples:
        AgentcoreCdkStack -> agentcore-cdk-stack
        MyHTTPSGateway    -> my-https-gateway
        mcp_calculator    -> mcp-calculator
    """
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1-\2", s)
    return s.lower().replace("_", "-")


def to_pascal_case(s: str) -> str:
    """Convert kebab-case, snake_case, or camelCase to PascalCase.

    Examples:
        skill-search       -> SkillSearch
        mcp_calculator     -> McpCalculator
        temperature-converter -> TemperatureConverter
    """
    parts = re.split(r"[-_]", s)
    return "".join(part.capitalize() for part in parts)


def to_snake_case(s: str) -> str:
    """Convert PascalCase, camelCase, or kebab-case to snake_case.

    Required for AgentCore Runtime names (only letters, numbers, underscores allowed).

    Examples:
        AgentcoreCdkStack -> agentcore_cdk_stack
        mcp-calculator    -> mcp_calculator
    """
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower().replace("-", "_")
