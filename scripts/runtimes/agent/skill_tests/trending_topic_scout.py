"""Skill: Trending Topic Scout — search repos, calculate spread/midpoint, convert to temperature."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "How's the momentum on rust web frameworks?"
    # "Is rust web framework trending?"
)
