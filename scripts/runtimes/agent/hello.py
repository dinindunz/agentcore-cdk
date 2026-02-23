"""Skill: Issue Heat Map — analyze issues and PRs, calculate maintenance burden index."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "Hello AgentCore!"
)
