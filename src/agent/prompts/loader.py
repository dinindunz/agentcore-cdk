"""Load system prompt from markdown file.

This module provides functionality to load the base system prompt from a
markdown file and optionally append dynamic sections like skills summaries.
"""

from pathlib import Path

from common.logger import logger


def load_system_prompt(skills_section: str = "") -> str:
    """
    Load system prompt from markdown file and append optional sections.

    Reads the base system prompt from system_prompt.md and appends any
    additional sections (e.g., skills summary) provided as arguments.

    Args:
        skills_section: Optional skills section to append to the base prompt
            (default: empty string)

    Returns:
        Complete system prompt string with all sections combined

    Raises:
        FileNotFoundError: If system_prompt.md cannot be found
        IOError: If the file cannot be read

    Example:
        # Load base prompt only
        prompt = load_system_prompt()

        # Load with skills section
        skills = load_skills_summary(config)
        prompt = load_system_prompt(skills_section=skills)
    """
    try:
        # Get the directory containing this file
        prompts_dir = Path(__file__).parent

        # Read the system prompt markdown file
        prompt_file = prompts_dir / "system_prompt.md"
        base_prompt = prompt_file.read_text(encoding="utf-8")

        logger.info(f"[Prompts] Loaded system prompt: file={prompt_file.name}")

        # Append skills section if provided
        if skills_section:
            return base_prompt + skills_section

        return base_prompt

    except Exception as e:
        logger.error(f"[Prompts] Failed to load system prompt: {e}")
        # Fallback to minimal prompt if file loading fails
        return "You are a helpful assistant."
