"""AgentCore runtime entry point.

This module provides the minimal orchestration layer for the AgentCore agent
runtime. It initialises the BedrockAgentCoreApp, sets up MCP clients, loads
configuration and tools, creates the agent, and wires everything together.

The actual invocation logic is delegated to the agent_handler module for better
testability and maintainability.
"""

from agent_handler import invoke_agent
from auth.sigv4 import SigV4Auth
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from config import get_config
from gateway.clients import load_all_tools, setup_mcp_clients
from prompts.loader import load_system_prompt
from strands import Agent

from memory.short_term import ShortTermMemory
from skills.loader import load_skills_summary

# Initialise Bedrock AgentCore app
app = BedrockAgentCoreApp()

# Global state for lazy initialization
_initialized = False
_agent: Agent | None = None
_memory: ShortTermMemory | None = None


def _initialize() -> None:
    """
    Lazy initialization of agent and dependencies.

    Initialises the agent, MCP clients, tools, and memory on first invocation.
    Subsequent calls are no-ops. Thread-safe for multiple workers in AgentCore.
    """
    global _initialized, _agent, _memory

    if _initialized:
        return

    # Load configuration
    config = get_config()

    # Setup authentication
    sigv4_auth = SigV4Auth(region=config.region_name)

    # Setup MCP clients
    jwt_client, iam_client = setup_mcp_clients(config, sigv4_auth)

    # Load tools from both gateways
    tools = load_all_tools(jwt_client, iam_client)

    # Load system prompt and skills summary
    skills_section = load_skills_summary(config)
    system_prompt = load_system_prompt(skills_section=skills_section)

    # Create agent with tools and system prompt
    _agent = Agent(tools=tools, system_prompt=system_prompt)

    # Initialise memory (only if configured)
    if config.memory_id:
        _memory = ShortTermMemory(memory_id=config.memory_id, region_name=config.region_name)

    _initialized = True


@app.entrypoint
def invoke(payload):
    """
    AgentCore runtime entrypoint.

    Processes incoming requests with the agent invocation handler, which manages
    conversation context, prompt enhancement, agent execution, and memory storage.

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
    # Lazy initialize on first invocation
    _initialize()

    return invoke_agent(_agent, payload, _memory)


# Start the runtime
app.run()
