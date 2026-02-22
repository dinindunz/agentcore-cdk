"""Skill: Trending Topic Scout — search repos, calculate spread/midpoint, convert to temperature."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "Search GitHub for repositories about 'rust web framework'. "
    "Take the top result's star count and the lowest result's star count. "
    "Calculate the spread and midpoint, then convert the midpoint "
    "from Celsius to Fahrenheit to gauge topic momentum."
)
