"""Skill: Portfolio Summary — list user repos, calculate total/average stars, derive temperature."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "What's my GitHub portfolio temperature?"
    # "How's my GitHub portfolio doing?"
)
