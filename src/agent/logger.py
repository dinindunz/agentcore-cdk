"""Structured logging for AgentCore components.

This module provides structured logging functions that wrap print() to maintain
consistency with existing codebase patterns while providing better organisation
and reusability.

Example:
    from logger import log, log_error, log_invocation

    log("Agent", "Processing request", request_id="abc123")
    log_invocation("Gateway", endpoint="https://example.com", method="POST")
    log_error("Memory", "Failed to retrieve context", error)
"""

from typing import Any


def log(component: str, message: str, **kwargs: Any) -> None:
    """
    Log a message with component context.

    Formats and prints a structured log message with optional key-value pairs.
    Format: [Component] Message: key=value key2=value2

    Args:
        component: Component name (e.g., "Agent", "Memory", "Gateway")
        message: Log message
        **kwargs: Additional key-value pairs to include in log output

    Example:
        log("Agent", "Processing request", user="john", session="xyz")
        # Output: [Agent] Processing request: user=john session=xyz
    """
    if kwargs:
        # Format key-value pairs as: key=value key2=value2
        extras = " ".join(f"{key}={value}" for key, value in kwargs.items())
        print(f"[{component}] {message}: {extras}")
    else:
        print(f"[{component}] {message}")


def log_error(component: str, message: str, error: Exception) -> None:
    """
    Log an error with exception details.

    Args:
        component: Component name
        message: Error context message
        error: The exception that occurred

    Example:
        try:
            process_data()
        except ValueError as e:
            log_error("Agent", "Failed to process data", e)
            # Output: [Agent] ERROR: Failed to process data: invalid value
    """
    print(f"[{component}] ERROR: {message}: {error}")


def log_invocation(component: str, **kwargs: Any) -> None:
    """
    Log an invocation event with structured parameters.

    Convenience function for logging service/function invocations with
    structured parameters.

    Args:
        component: Component name
        **kwargs: Key-value pairs describing the invocation context

    Example:
        log_invocation("Agent", actor="user123", session="sess456")
        # Output: [Agent] Invoked: actor=user123 session=sess456
    """
    if kwargs:
        extras = " ".join(f"{key}={value}" for key, value in kwargs.items())
        print(f"[{component}] Invoked: {extras}")
    else:
        print(f"[{component}] Invoked")
