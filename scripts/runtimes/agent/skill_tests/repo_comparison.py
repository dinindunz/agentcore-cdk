"""Skill: Repo Comparison — compare two repos by stars with calculated metrics."""

from invoke_agent import invoke_agent

invoke_agent(
    "Compare the GitHub repos facebook/react and vuejs/vue. "
    "Get their star counts, calculate the difference, the ratio, "
    "and each repo's percentage share of the combined total."
)
