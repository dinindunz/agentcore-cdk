"""Skills loading modules.

This package provides functionality for loading skill definitions from S3
and generating system prompt sections that describe available skills to the agent.
"""

from .loader import load_skills_summary

__all__ = ["load_skills_summary"]
