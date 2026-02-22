"""Skill: Issue Heat Map — analyze issues and PRs, calculate maintenance burden index."""

from invoke_agent import invoke_agent

invoke_agent(
    "For the repo kubernetes/kubernetes, list the open issues and open pull requests. "
    "Calculate the issue-to-PR ratio, multiply it by 10, "
    "and convert the result from Fahrenheit to Celsius as a maintenance burden index."
)
