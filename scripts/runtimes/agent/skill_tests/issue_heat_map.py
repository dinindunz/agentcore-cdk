"""Skill: Issue Heat Map — analyse issues and PRs, calculate maintenance burden index."""

import sys
from pathlib import Path

# Add parent directory to path to import invoke_agent module
sys.path.insert(0, str(Path(__file__).parent.parent))
from invoke_agent import invoke_agent

invoke_agent(
    "What's the maintenance burden for kubernetes/kubernetes?"
    # "How heavy is the maintenance load on the kubernetes repo?"
)
