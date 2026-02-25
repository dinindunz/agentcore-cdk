"""Load skills from S3 for agent system prompt.

This module provides functionality to scan an S3 bucket for skill definition
markdown files, extract their titles and descriptions, and format them into
a system prompt section that describes available skills to the agent.

Example:
    from config import get_config
    from skills.loader import load_skills_summary

    config = get_config()
    skills_section = load_skills_summary(config)
    system_prompt = base_prompt + skills_section
"""

from ..config import AgentConfig
from ..logger import log, log_error


def load_skills_summary(config: AgentConfig) -> str:
    """
    Load skill markdown files from S3 and build a summary for the system prompt.

    Scans the configured skills bucket for .md files, extracts titles (first H1
    heading) and descriptions (first non-heading line after the title), and
    formats them as a bulleted list for inclusion in the agent's system prompt.

    Args:
        config: Agent configuration with skills bucket name

    Returns:
        Formatted skills section for system prompt, or empty string if:
        - No skills bucket is configured
        - The bucket is empty or contains no .md files
        - An error occurs while loading skills

    Example output:
        ## Available Skills

        When a user's request matches a skill, use the skill-search___search_skills
        tool to retrieve the full step-by-step instructions, then follow them.

        - **Weather Lookup**: Get current weather for a location
        - **Code Review**: Analyse code for best practices and potential bugs

    Example:
        config = get_config()

        # With skills bucket configured
        summary = load_skills_summary(config)
        system_prompt = base_prompt + summary

        # Without skills bucket
        config.skills_bucket = None
        summary = load_skills_summary(config)  # Returns ""
    """
    if not config.skills_bucket:
        return ""

    try:
        # List all objects in the skills bucket
        response = config.s3_client.list_objects_v2(Bucket=config.skills_bucket)
        contents = response.get("Contents", [])

        if not contents:
            log("Skills", "No objects found in skills bucket", bucket=config.skills_bucket)
            return ""

        lines = []
        for obj in contents:
            key = obj["Key"]

            # Only process markdown files
            if not key.endswith(".md"):
                continue

            try:
                # Download and decode the skill file
                body = (
                    config.s3_client.get_object(Bucket=config.skills_bucket, Key=key)["Body"]
                    .read()
                    .decode()
                )

                # Extract title (first H1) and description (first non-empty line after title)
                title = ""
                description = ""
                for line in body.strip().split("\n"):
                    stripped = line.strip()

                    # Look for first H1 heading
                    if stripped.startswith("# ") and not title:
                        title = stripped[2:].strip()
                    # After finding title, look for first non-heading line
                    elif title and stripped and not stripped.startswith("#"):
                        description = stripped
                        break

                # Only add to summary if we found a valid title
                if title:
                    lines.append(f"- **{title}**: {description}")

            except Exception as e:
                log_error("Skills", f"Failed to process skill file: {key}", e)
                # Continue processing other files even if one fails
                continue

        # If no valid skills were found, return empty string
        if not lines:
            log("Skills", "No valid skill definitions found in bucket")
            return ""

        # Build the skills section
        skills_list = "\n".join(lines)
        return (
            "\n\n## Available Skills\n"
            "When a user's request matches a skill, use the skill-search___search_skills tool to "
            "retrieve the full step-by-step instructions, then follow them.\n\n" + skills_list
        )

    except Exception as e:
        log_error("Skills", "Failed to load skills from S3", e)
        return ""
