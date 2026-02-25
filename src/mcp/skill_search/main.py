import os
import re

import boto3

SKILLS_BUCKET = os.environ["SKILLS_BUCKET"]

s3_client = boto3.client("s3")

# Module-level cache for warm Lambda starts
_cached_skills: list[dict] | None = None


def _load_skills() -> list[dict]:
    """Load all markdown skill files from S3 and parse them."""
    global _cached_skills
    if _cached_skills is not None:
        return _cached_skills

    resp = s3_client.list_objects_v2(Bucket=SKILLS_BUCKET)
    skills = []
    for obj in resp.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".md"):
            continue
        body = s3_client.get_object(Bucket=SKILLS_BUCKET, Key=key)["Body"].read().decode()
        skill = _parse_skill_markdown(body)
        skill["file"] = key
        skills.append(skill)

    _cached_skills = skills
    return _cached_skills


def _parse_skill_markdown(content: str) -> dict:
    """Parse a skill markdown file into a structured dict."""
    lines = content.strip().split("\n")
    title = ""
    description = ""
    parameters = []
    steps = []
    tools_used = []

    current_section = None

    for line in lines:
        stripped = line.strip()

        # Title: first H1
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
            current_section = "description"
            continue

        # Section headers
        if stripped.startswith("## "):
            header = stripped[3:].strip().lower()
            if "parameter" in header:
                current_section = "parameters"
            elif "step" in header:
                current_section = "steps"
            elif "tool" in header:
                current_section = "tools_used"
            else:
                current_section = None
            continue

        # Parse content based on current section
        if current_section == "description" and stripped:
            description = stripped

        elif current_section == "parameters" and stripped.startswith("- "):
            param = stripped[2:].strip()
            if param.lower() != "none":
                parameters.append(param)

        elif current_section == "steps" and re.match(r"^\d+\.\s", stripped):
            step = re.sub(r"^\d+\.\s*", "", stripped)
            steps.append(step)

        elif current_section == "tools_used" and stripped.startswith("- "):
            tools_used.append(stripped[2:].strip())

    return {
        "title": title,
        "description": description,
        "parameters": parameters,
        "steps": steps,
        "tools_used": tools_used,
        "content": content,
    }


def handler(event, context):
    """Search skills by keyword query. Returns matching skills sorted by relevance."""
    query = event.get("query", "").lower()
    skills = _load_skills()

    if not query:
        return {"skills": skills}

    keywords = query.split()
    scored = []
    for skill in skills:
        searchable = " ".join(
            [
                skill["title"].lower(),
                skill["description"].lower(),
                " ".join(skill["tools_used"]).lower(),
                " ".join(skill["parameters"]).lower(),
            ]
        )
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, skill))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [s for _, s in scored]

    return {"skills": results, "count": len(results)}
