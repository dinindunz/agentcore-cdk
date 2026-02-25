"""GitHub Data Integrity Evaluator

Validates that the agent accurately reports GitHub data without hallucination.
Compares agent claims against actual API responses to detect fabricated
repository names, incorrect star counts, or invented metadata.
"""

# Evaluator configuration
EVALUATOR_NAME = "GitHubDataIntegrity"
EVALUATION_LEVEL = "trace"  # Evaluate full trace with API responses

# Model configuration
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
TEMPERATURE = 0.0  # Deterministic for strict validation
TOP_P = 0.95
MAX_TOKENS = 1536  # Medium-length explanations with examples

# Scoring schema
SCORING_TYPE = "numbered_scale"
MIN_VALUE = 1
MAX_VALUE = 5
SCORING_DESCRIPTION = "1=Major hallucination, 5=Perfect data integrity"

# Description
DESCRIPTION = "Detects hallucinated or incorrect GitHub data"

# Evaluation prompt
PROMPT = """You are evaluating whether the agent accurately reported GitHub data without hallucination.

TRACE CONTEXT:
{context}

VALIDATION CATEGORIES:

1. REPOSITORY NAMES/OWNERS (Critical):
   - Are repository names in agent response actually present in API responses?
   - Are owner names spelled correctly (exact match)?
   - Did agent invent repositories not returned by API?
   - Example hallucination: Claiming "facebook/react" when API returned "vercel/next.js"

2. STAR COUNTS (Critical):
   - Do reported star counts EXACTLY match API response values?
   - If calculations done (sums, averages), are they arithmetically correct?
   - Example hallucination: API says 45,231 stars but agent reports "approximately 50,000"
   - Example error: Sum should be 12,500 but agent reports 13,000

3. ISSUE/PR COUNTS (Critical):
   - Do reported counts match API list lengths or returned values?
   - No fabricated issue counts or PR counts?
   - Example error: API returns 23 issues but agent claims 25

4. REPOSITORY METADATA (Important):
   - Descriptions match API data (if mentioned)?
   - Languages match API data (if mentioned)?
   - Topics/tags match API data (if mentioned)?
   - Example hallucination: Claiming repo is "TypeScript" when API shows "JavaScript"

5. CONSISTENCY (Important):
   - If same repo queried multiple times, are values consistent?
   - No contradictions between tool outputs and agent claims?
   - Example error: First mentions "1,234 stars" then later says "over 2,000 stars"

COMMON HALLUCINATION PATTERNS TO DETECT:

❌ Rounding to "nice numbers":
   - API: 4,567 stars → Agent: "approximately 5,000 stars" (WRONG)
   - API: 1,234 stars → Agent: "about 1,200 stars" (WRONG)

❌ Inventing popular repositories:
   - API returns: [repo-a, repo-b, repo-c]
   - Agent claims: "including the popular repo-d" (WRONG - not in API response)

❌ Inflating metrics:
   - API: 234 stars → Agent: "highly popular with 300+ stars" (WRONG)

❌ Fabricating details:
   - API: No description → Agent: "This repo provides..." (WRONG - invented)

✅ Acceptable transformations:
   - API: 12500 → Agent: "12,500" (formatting OK)
   - API: stargazers_count: 123 → Agent: "123 stars" (labeling OK)
   - API: full_name: "owner/repo" → Agent: "owner/repo" (exact match OK)

VALIDATION PROCESS:
1. Extract all factual claims from agent response (numbers, names, metadata)
2. For each claim, find the source in API responses
3. Verify exact match (or acceptable transformation)
4. Flag any claims that cannot be traced to API responses
5. Flag any numeric discrepancies (even minor ones)

SCORING:
5 = Perfect integrity: All data exactly traceable to API responses, no hallucinations
4 = Minor formatting: Data correct but minor presentation differences (e.g., "12500" vs "12,500")
3 = Small discrepancy: One or two minor data mismatches (e.g., rounded one number)
2 = Multiple errors: Several hallucinated values or incorrect calculations
1 = Major hallucination: Fabricated repositories, completely wrong data, or multiple serious errors

ANALYSIS FORMAT:
1. List all factual claims in agent response
2. For each claim, cite the API source (or mark as "HALLUCINATION")
3. Flag any discrepancies with examples
4. Provide final score with reasoning

IMPORTANT:
- Be strict: Even "approximately" or "about" counts as hallucination if not exact
- Numbers must match exactly (no rounding unless agent explicitly states "approximately")
- Repository names must match character-for-character
- If agent adds information not in API, flag it (unless clearly inference/calculation)

Provide your score (1-5) and detailed analysis with specific examples."""
