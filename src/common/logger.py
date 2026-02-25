"""Structured logging for AgentCore components.

This module provides a configured logger with structured formatting and
configurable log levels via environment variables.

Environment Variables:
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               Defaults to INFO if not set

Example:
    from common.logger import logger

    logger.info("[Calculator] Add operation: a=5 b=3 result=8")
    logger.debug("[SkillSearch] Using cached skills: count=10")
    logger.error("[TempConverter] Invalid input: event={'bad': 'data'}")
    logger.warning("[Agent] Rate limit approaching: remaining=10")
"""

import logging
import os
import sys


def _configure_logger() -> logging.Logger:
    """
    Configure and return a logger instance with structured formatting.

    The logger is configured based on the LOG_LEVEL environment variable
    (defaults to INFO). Log messages are formatted with component context.

    Returns:
        Configured logger instance
    """
    # Get log level from environment variable (default to INFO)
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        log_level = "INFO"

    # Create logger
    logger_instance = logging.getLogger("agentcore")
    logger_instance.setLevel(getattr(logging, log_level))

    # Avoid adding handlers multiple times if logger already configured
    if not logger_instance.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level))

        # Create formatter - simple format for CloudWatch Logs
        # CloudWatch will add timestamp, so we just need level and message
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)

        # Add handler to logger
        logger_instance.addHandler(handler)

    return logger_instance


# Create global logger instance
logger = _configure_logger()
