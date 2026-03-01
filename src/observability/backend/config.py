"""Configuration management for observability dashboard."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from project root .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Dashboard configuration."""

    # AWS Configuration
    AWS_REGION = os.getenv("REGION_NAME", "ap-southeast-2")

    # Server Configuration
    PORT = int(os.getenv("OBSERVABILITY_PORT", 5000))
    AUTO_OPEN_BROWSER = os.getenv("OBSERVABILITY_AUTO_OPEN", "true").lower() == "true"
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # Query Configuration
    CACHE_TTL_SECONDS = int(os.getenv("OBSERVABILITY_CACHE_TTL_SECONDS", 900))
    DEFAULT_HOURS = int(os.getenv("OBSERVABILITY_DEFAULT_HOURS", 24))
    MAX_SESSIONS = int(os.getenv("OBSERVABILITY_MAX_SESSIONS", 100))

    # CloudWatch Log Groups
    RUNTIME_LOG_PREFIX = "/aws/bedrock-agentcore/runtimes/"
    SPANS_LOG_GROUP = "aws/spans"
