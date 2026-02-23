"""Skill: Repo Hotness Rating — search repos by topic, scale stars, convert to temperature."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "Show me the hottest machine learning repos on GitHub"
    # "What are the top ML projects right now?"
)
