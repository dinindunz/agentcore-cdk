"""AgentCore runtime entry point.

This module provides the minimal orchestration layer for the AgentCore agent
runtime. It initialises the BedrockAgentCoreApp, sets up MCP clients, loads
configuration and tools, creates the agent, and wires everything together.

The actual invocation logic is delegated to the agent_handler module for better
testability and maintainability.
"""

from agent_handler import invoke_agent_with_session_manager
from auth.sigv4 import SigV4Auth
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from gateway.clients import load_all_tools, setup_mcp_clients
from prompts.loader import load_system_prompt

from config import get_config
from skills.loader import load_skills_summary

# Initialise Bedrock AgentCore app
app = BedrockAgentCoreApp()

# Global state for lazy initialization (MCP clients, tools, prompts only)
_initialized = False
_config = None
_tools = None
_system_prompt = None


def _initialize() -> None:
    """
    Lazy initialization of global dependencies.

    Initialises MCP clients, tools, and system prompt on first invocation.
    These are expensive to create, so we do them once per container.
    Agent instances are created per request with session managers.
    """
    global _initialized, _config, _tools, _system_prompt

    if _initialized:
        return

    # Load configuration
    _config = get_config()

    # Setup authentication
    sigv4_auth = SigV4Auth(region=_config.region_name)

    # Setup MCP clients (heavy operation - do once)
    jwt_client, iam_client = setup_mcp_clients(_config, sigv4_auth)

    # Load tools from both gateways (heavy operation - do once)
    _tools = load_all_tools(jwt_client, iam_client)

    # Load system prompt and skills summary (do once)
    skills_section = load_skills_summary(_config)
    _system_prompt = load_system_prompt(skills_section=skills_section)

    _initialized = True


@app.entrypoint
def invoke(payload):
    """
    AgentCore runtime entrypoint with session manager.

    Processes incoming requests by creating an agent instance with session manager
    for automatic memory handling. MCP clients, tools, and prompts are initialized
    globally once per container for performance.

    Args:
        payload: Request payload from AgentCore runtime with fields:
            - prompt: User message (optional, default: "Hello")
            - actor_id: User identifier (optional, default: "default_actor")
            - session_id: Session identifier (optional, default: "default_session")

    Returns:
        Response dictionary with 'result' key containing agent response text

    Example payload:
        {
            "prompt": "What tools do you have access to?",
            "actor_id": "user123",
            "session_id": "sess456"
        }
    """
    # Lazy initialize global dependencies (once per container)
    _initialize()

    # Create agent with session manager (once per request)
    return invoke_agent_with_session_manager(
        config=_config,
        tools=_tools,
        system_prompt=_system_prompt,
        payload=payload,
    )


# Start the runtime
app.run()
