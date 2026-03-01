"""Core agent invocation handler with Strands SDK session manager.

This module creates agent instances per request with AgentCoreMemorySessionManager
for automatic conversation memory handling (short-term + long-term strategies).
"""

import os
from typing import Any

from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from strands import Agent
from strands.models.bedrock import BedrockModel

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
) -> dict[str, Any]:
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
        payload: Request payload with AgentCore standard format:
            - input.value: User message (default: "Hello")
            - actorId: User identifier (default: "default_actor")
            - sessionId: Session identifier (default: "default_session")

    Returns:
        Response dictionary with AgentCore standard format:
            {
                "output": {"value": text},
                "sessionId": session_id,
                "actorId": actor_id
            }
    """
    # Extract parameters from payload with defaults (AgentCore standard format)
    user_message = payload.get("input", {}).get("value", DEFAULT_USER_MESSAGE)
    actor_id = payload.get("actorId", DEFAULT_ACTOR_ID)
    session_id = payload.get("sessionId", DEFAULT_SESSION_ID)

    # Log invocation
    logger.info(f"[Agent] Invoked: actor={actor_id} session={session_id}")

    # Create session manager for automatic memory handling (if configured)
    session_manager = None
    if config.memory_id:
        # Load retrieval configuration from environment variables
        preference_top_k = int(os.environ["MEMORY_PREFERENCE_TOP_K"])
        preference_relevance_score = float(os.environ["MEMORY_PREFERENCE_RELEVANCE_SCORE"])
        semantic_top_k = int(os.environ["MEMORY_SEMANTIC_TOP_K"])
        semantic_relevance_score = float(os.environ["MEMORY_SEMANTIC_RELEVANCE_SCORE"])

        # Configure retrieval for long-term memory strategies
        # Map namespaces to retrieval configs for preference and semantic memory
        retrieval_config = {
            f"/preferences/{actor_id}/": RetrievalConfig(
                top_k=preference_top_k,
                relevance_score=preference_relevance_score,
            ),
            f"/facts/{actor_id}/": RetrievalConfig(
                top_k=semantic_top_k,
                relevance_score=semantic_relevance_score,
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

    # Create Bedrock model with inference profile (if available)
    model = BedrockModel(
        model_id=config.inference_profile_arn,
        max_tokens=config.model_max_tokens,
        temperature=config.model_temperature,
    )

    # Create agent with session manager (automatic memory!)
    agent = Agent(
        model=model,
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

    # Return AgentCore standard response format
    return {
        "output": {"value": text},
        "sessionId": session_id,
        "actorId": actor_id,
    }
