"""AgentCore agent runtime package.

This package provides a modular, well-structured implementation of an
AgentCore agent with memory integration, MCP tool access, and skill
execution capabilities.

Modules:
    - main: Runtime entry point and orchestration
    - config: Configuration management with lazy loading
    - logger: Structured logging utilities
    - agent_handler: Core invocation logic
    - auth: Authentication modules (Cognito OAuth2, SigV4)
    - gateway: MCP client setup and tool loading
    - skills: Skills loading from S3
    - memory: Conversation memory integration
"""

__version__ = "0.1.0"
