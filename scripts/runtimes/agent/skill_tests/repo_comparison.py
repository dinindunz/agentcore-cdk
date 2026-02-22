"""Skill: Repo Comparison — compare two repos by stars with calculated metrics."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "Compare the GitHub repos facebook/react and vuejs/vue. "
    "Get their star counts, calculate the difference, the ratio, "
    "and each repo's percentage share of the combined total."
)
