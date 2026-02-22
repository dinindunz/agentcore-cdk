"""Skill: Portfolio Summary — list user repos, calculate total/average stars, derive temperature."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "List my GitHub repositories, calculate the total star count across all repos, "
    "the average stars per repo, and convert the average from Celsius to Fahrenheit "
    "as a portfolio temperature."
)
