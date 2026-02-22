"""Skill: Portfolio Summary — list user repos, calculate total/average stars, derive temperature."""

from invoke_agent import invoke_agent

invoke_agent(
    "List my GitHub repositories, calculate the total star count across all repos, "
    "the average stars per repo, and convert the average from Celsius to Fahrenheit "
    "as a portfolio temperature."
)
