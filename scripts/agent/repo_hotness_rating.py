"""Skill: Repo Hotness Rating — search repos by topic, scale stars, convert to temperature."""

from invoke_agent import invoke_agent

invoke_agent(
    "Search GitHub for the top 3 repositories about 'machine learning', "
    "get their star counts, divide each by 1000, "
    "and convert each result from Celsius to Fahrenheit as a hotness score. "
    "Present the results in a table."
)
