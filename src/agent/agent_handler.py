"""Core agent invocation handler with Strands SDK session manager.

This module creates agent instances per request with AgentCoreMemorySessionManager
for automatic conversation memory handling (short-term + long-term strategies).
"""

from typing import Any

from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from strands import Agent

from common.logger import logger

# Default values for optional payload fields
DEFAULT_ACTOR_ID = "default_actor"
DEFAULT_SESSION_ID = "default_session"
DEFAULT_USER_MESSAGE = "Hello"


def extract_text_from_result(result: Any) -> str:
    """
    Extract text content from agent result message.

    Iterates through the agent's response content blocks and concatenates
    all text blocks into a single string.

    Args:
        result: Agent execution result with message content

    Returns:
        Concatenated text from all text content blocks, or empty string if
        no text content is present
    """
    return "".join(block["text"] for block in result.message.get("content", []) if "text" in block)


def invoke_agent_with_session_manager(
    config: Any,
    tools: list,
    system_prompt: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    """
    Process user input with agent using session manager for automatic memory.

    Creates a new agent instance with AgentCoreMemorySessionManager configured
    for the request's actor and session. The session manager automatically:
    - Retrieves short-term conversation context
    - Retrieves long-term memory (preferences, facts, summaries)
    - Enhances prompts with memory context
    - Stores events after agent execution

    Args:
        config: Application configuration with region and memory settings
        tools: List of tools loaded from MCP gateways (reused across requests)
        system_prompt: System prompt with skills (reused across requests)
        payload: Request payload with fields:
            - prompt: User message (default: "Hello")
            - actor_id: User identifier (default: "default_actor")
            - session_id: Session identifier (default: "default_session")

    Returns:
        Response dictionary with 'result' key containing agent response text
    """
    # Extract parameters from payload with defaults
    user_message = payload.get("prompt", DEFAULT_USER_MESSAGE)
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = payload.get("session_id", DEFAULT_SESSION_ID)

    # Log invocation
    logger.info(f"[Agent] Invoked: actor={actor_id} session={session_id}")

    # Create session manager for automatic memory handling (if configured)
    session_manager = None
    if config.memory_id:
        # Configure retrieval for long-term memory strategies
        # Map namespaces to retrieval configs for preference and semantic memory
        retrieval_config = {
            f"/preferences/{actor_id}/": RetrievalConfig(
                top_k=10,  # Retrieve up to 10 preference records
                relevance_score=0.2,  # Minimum relevance threshold
            ),
            f"/facts/{actor_id}/": RetrievalConfig(
                top_k=10,  # Retrieve up to 10 semantic facts
                relevance_score=0.2,
            ),
        }

        agentcore_memory_config = AgentCoreMemoryConfig(
            memory_id=config.memory_id,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config=retrieval_config,  # Namespace-specific retrieval configs
        )
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=agentcore_memory_config,
            region_name=config.region_name,
        )

    # Create agent with session manager (automatic memory!)
    agent = Agent(
        tools=tools,
        system_prompt=system_prompt,
        session_manager=session_manager,
    )

    # Execute agent (session manager handles context retrieval and storage automatically)
    result = agent(user_message)

    # Extract text from agent response
    text = extract_text_from_result(result)

    # Log completion
    logger.info("[Agent] Completed")

    return {"result": text}
