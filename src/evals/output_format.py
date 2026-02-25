"""Structured Output Format Evaluator

Validates that the agent's response includes all required fields and uses
proper formatting (units, decimal places, structure) as defined in the skill.
"""

# Evaluator configuration
EVALUATOR_NAME = "StructuredOutputFormat"
EVALUATION_LEVEL = "trace"  # Evaluate full response

# Model configuration
MODEL_ID = "anthropic.claude-haiku-4-5-v1:0"  # Fast for format checking
TEMPERATURE = 0.0  # Deterministic
TOP_P = 0.9
MAX_TOKENS = 512  # Short explanations

# Scoring schema
SCORING_TYPE = "binary"
SCORING_DESCRIPTION = "Yes if properly formatted, No if missing fields or wrong format"

# Description
DESCRIPTION = "Validates response contains required fields and proper formatting"

# Evaluation prompt
PROMPT = """You are evaluating whether the agent's response follows the expected output format.

TRACE CONTEXT:
- User request: {input}
- Agent response: {output}

FORMAT REQUIREMENTS BY SKILL:

1. ISSUE HEAT MAP (owner/repo):
   Required fields:
   ✓ Issue count (numeric)
   ✓ Pull request count (numeric)
   ✓ Issue-to-PR ratio (numeric with decimals)
   ✓ Maintenance burden temperature with °C unit
   Format requirements:
   - Temperature must include °C symbol
   - Ratio should show at least 2 decimal places
   - Clear labels for each metric

2. PORTFOLIO SUMMARY:
   Required fields:
   ✓ Total repository count (numeric)
   ✓ Total stars (numeric)
   ✓ Average stars per repo (numeric with decimals)
   ✓ Portfolio temperature with °F unit
   Format requirements:
   - Temperature must include °F symbol
   - Average should show at least 2 decimal places
   - Clear summary structure

3. REPO HOTNESS RATING (topic):
   Required fields:
   ✓ Table or list with 3 repositories (or explanation if fewer)
   ✓ For each: repository name, star count, scaled value, hotness in °F
   Format requirements:
   - Structured presentation (table preferred)
   - All hotness values must include °F symbol
   - Repository names in owner/repo format

4. REPO COMPARISON (owner1/repo1, owner2/repo2):
   Required fields:
   ✓ Star count for repository 1
   ✓ Star count for repository 2
   ✓ Star count difference
   ✓ Star count ratio
   ✓ Percentage share for each repository
   Format requirements:
   - Percentages should add up to approximately 100%
   - Clear comparison structure
   - Both repositories clearly identified

5. TRENDING TOPIC SCOUT (topic):
   Required fields:
   ✓ Top repository name and star count
   ✓ Bottom repository name and star count
   ✓ Spread (difference)
   ✓ Midpoint
   ✓ Momentum temperature with °F unit
   Format requirements:
   - Temperature must include °F symbol
   - Repository names in owner/repo format
   - Clear presentation of spread and midpoint

GENERAL FORMAT REQUIREMENTS:

Units:
- Temperatures MUST include unit symbol (°C or °F)
- Correct unit for each skill (Issue Heat Map uses °C, others use °F)

Numeric Precision:
- Decimals: At least 2 decimal places for non-integers
- Example: 3.33, not 3.3
- Whole numbers can be integers (no forced decimals)

Structure:
- Clear section headers or labels
- Organized presentation (not just a paragraph of numbers)
- No truncated or incomplete responses
- All requested metrics present

Repository Names:
- Format: owner/repo (e.g., "facebook/react")
- Not just "react" or "React repo"

EVALUATION PROCESS:
1. Identify which skill was executed
2. Check for presence of ALL required fields
3. Verify correct units (°C or °F as specified)
4. Verify numeric precision (2+ decimals for non-integers)
5. Assess overall structure and clarity

SCORING:
Yes = Response includes all required fields with proper units, precision, and structure
No = Missing one or more required fields, wrong units, insufficient precision, or poor structure

COMMON FORMAT ISSUES TO FLAG:
❌ Missing temperature units: "Temperature: 25" instead of "Temperature: 25°C"
❌ Wrong units: "25°F" when skill requires °C
❌ Insufficient precision: "3.3" instead of "3.33"
❌ Missing fields: Ratio not reported, percentage shares omitted
❌ Poor structure: All numbers in a paragraph, no clear labels
❌ Incomplete: Response cuts off mid-calculation

✅ Acceptable formats:
- "Temperature: 25.00°C" or "Temperature: 25°C" (both OK for integers)
- "Ratio: 3.33" or "Ratio: 3.333" (more precision is OK)
- Table format or bullet list (both OK)

ANALYSIS FORMAT:
1. List required fields for the skill
2. Mark each as PRESENT or MISSING
3. Check units and precision
4. Provide Yes/No with reasoning

Provide Yes/No and brief explanation."""
