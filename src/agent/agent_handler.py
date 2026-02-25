"""Core agent invocation handler with conversation memory integration.

This module provides the main agent execution logic, broken down into composable
functions for building context, enhancing prompts, extracting results, and storing
interactions in memory.
"""

from typing import Any

from strands import Agent

from common.logger import logger
from memory.short_term import ShortTermMemory

# Default values for optional payload fields
DEFAULT_ACTOR_ID = "default_actor"
DEFAULT_SESSION_ID = "default_session"
DEFAULT_USER_MESSAGE = "Hello"


def build_context_from_memory(
    memory: ShortTermMemory,
    actor_id: str,
    session_id: str,
    max_turns: int = 5,
) -> str:
    """
    Retrieve recent conversation context from memory.

    Fetches the most recent conversation turns from memory and formats them
    as a context string with role labels (USER/ASSISTANT) for inclusion in
    the agent's prompt.

    Args:
        memory: Memory client instance
        actor_id: User identifier
        session_id: Session identifier
        max_turns: Maximum number of conversation turns to retrieve (default: 5)

    Returns:
        Formatted conversation context string with newline-separated turns,
        or empty string if no context is available or an error occurs

    Example output:
        USER: What's the weather like today?
        ASSISTANT: I'll check that for you.
        USER: Thanks!
    """
    try:
        recent_events = memory.get_recent_context(
            actor_id=actor_id,
            session_id=session_id,
            max_turns=max_turns,
        )

        # Build context string from recent events
        context_messages = []
        for event in recent_events:
            for turn in event.get("payload", []):
                if "conversational" in turn:
                    role = turn["conversational"]["role"]
                    text = turn["conversational"]["content"].get("text", "")
                    context_messages.append(f"{role}: {text}")

        if context_messages:
            return "\n".join(context_messages) + "\n\n"
        return ""

    except Exception as e:
        logger.error(f"[Memory] Error retrieving context: {e}")
        return ""


def enhance_prompt_with_context(user_message: str, context: str) -> str:
    """
    Prepend conversation context to user message.

    Combines historical conversation context with the current user message
    to provide the agent with full conversational context.

    Args:
        user_message: Current user message
        context: Historical conversation context from memory

    Returns:
        Enhanced prompt with context prepended, or original message if no context
    """
    if context:
        return f"{context}USER: {user_message}"
    return user_message


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


def store_interaction_in_memory(
    memory: ShortTermMemory,
    actor_id: str,
    session_id: str,
    user_message: str,
    assistant_response: str,
) -> None:
    """
    Store user-assistant interaction in memory.

    Persists the conversation turn (user message and assistant response) to
    AgentCore Memory for future context retrieval.

    Args:
        memory: Memory client instance
        actor_id: User identifier
        session_id: Session identifier
        user_message: User's input message
        assistant_response: Agent's response text
    """
    try:
        memory.create_event(
            actor_id=actor_id,
            session_id=session_id,
            messages=[(user_message, "USER"), (assistant_response, "ASSISTANT")],
        )
    except Exception as e:
        logger.error(f"[Memory] Error storing event: {e}")


def invoke_agent(
    agent: Agent,
    payload: dict[str, Any],
    memory: ShortTermMemory | None,
) -> dict[str, str]:
    """
    Process user input and return an agent response.

    This is the main agent invocation handler that orchestrates the full
    request-response cycle:
    1. Extract parameters from payload
    2. Log invocation details
    3. Retrieve conversation context from memory (if enabled)
    4. Enhance user prompt with historical context
    5. Execute agent with enhanced prompt
    6. Extract text response from agent result
    7. Store interaction in memory (if enabled)
    8. Log completion and return result

    Args:
        agent: Configured strands Agent instance with tools and system prompt
        payload: Request payload with fields:
            - prompt: User message (default: "Hello")
            - actor_id: User identifier (default: "default_actor")
            - session_id: Session identifier (default: "default_session")
        memory: Optional memory client for conversation context. If None,
            context retrieval and storage are skipped.

    Returns:
        Response dictionary with 'result' key containing agent response text
    """
    # Extract parameters from payload with defaults
    user_message = payload.get("prompt", DEFAULT_USER_MESSAGE)
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = payload.get("session_id", DEFAULT_SESSION_ID)

    # Log invocation
    logger.info(f"[Agent] Invoked: actor={actor_id} session={session_id}")

    # Retrieve recent conversation context (if memory is enabled)
    context = ""
    if memory:
        context = build_context_from_memory(
            memory=memory,
            actor_id=actor_id,
            session_id=session_id,
            max_turns=5,
        )

    # Enhance prompt with conversation context
    enhanced_prompt = enhance_prompt_with_context(user_message, context)

    # Execute agent with enhanced prompt
    result = agent(enhanced_prompt)

    # Extract text from agent response
    text = extract_text_from_result(result)

    # Store this interaction in memory (if memory is enabled)
    if memory:
        store_interaction_in_memory(
            memory=memory,
            actor_id=actor_id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=text,
        )

    # Log completion
    logger.info("[Agent] Completed")

    return {"result": text}
