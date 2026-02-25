"""Skill Workflow Completeness Evaluator

Validates that the agent completed all required steps defined in the skill.
Ensures GitHub analysis skills follow the documented workflow and don't skip
critical steps in data gathering, calculation, or presentation.
"""

# Evaluator configuration
EVALUATOR_NAME = "SkillWorkflowCompleteness"
EVALUATION_LEVEL = "trace"  # Evaluate entire conversation trace

# Model configuration
MODEL_ID = (
    "anthropic.claude-opus-4-6-v1:0"  # Most capable for complex workflow analysis
)
TEMPERATURE = 0.1  # Slight variation for nuanced judgment
TOP_P = 0.95
MAX_TOKENS = 2048  # Longer explanations for detailed workflow analysis

# Scoring schema
SCORING_TYPE = "numbered_scale"
MIN_VALUE = 1
MAX_VALUE = 5
SCORING_DESCRIPTION = "1=Workflow not followed, 5=Perfect execution"

# Description
DESCRIPTION = "Validates agent followed skill workflow completely"

# Evaluation prompt
PROMPT = """You are evaluating whether the agent completed all required steps in a GitHub analysis skill.

TRACE CONTEXT:
- User request: {input}
- Agent response: {output}
- Tools called: {tool_calls}

SKILL DEFINITIONS:

1. ISSUE HEAT MAP (owner/repo)
   Purpose: Calculate maintenance burden as temperature
   Required steps:
   a) Call listIssues with state=open for the repository
   b) Call listPullRequests with state=open for the repository
   c) Use calculator divide: issues ÷ PRs to get ratio
   d) Use calculator multiply: ratio × 10
   e) Use temperature converter: fahrenheit_to_celsius for burden index
   f) Present results with: issue count, PR count, ratio, temperature in °C

2. PORTFOLIO SUMMARY
   Purpose: Summarise user's GitHub portfolio with star metrics
   Required steps:
   a) Call listAuthenticatedUserRepos to get all repositories
   b) Use calculator add repeatedly to sum total stars across repos
   c) Use calculator divide: total stars ÷ repo count for average
   d) Use temperature converter: celsius_to_fahrenheit for portfolio temperature
   e) Present: total repos, total stars, average stars, temperature in °F

3. REPO HOTNESS RATING (topic)
   Purpose: Find hot repositories and rate them with temperature
   Required steps:
   a) Call searchRepositories for topic, sorted by stars, limit to 3 results
   b) For each result, call getRepository to get star count
   c) Use calculator divide: star count ÷ 1000 for each repo
   d) Use temperature converter: celsius_to_fahrenheit for each scaled value
   e) Present table with: repo name, stars, scaled value, hotness in °F

4. REPO COMPARISON (owner1/repo1, owner2/repo2)
   Purpose: Compare two repositories by star metrics
   Required steps:
   a) Call getRepository for first repository
   b) Call getRepository for second repository
   c) Use calculator subtract: stars1 - stars2 for difference
   d) Use calculator divide: stars1 ÷ stars2 for ratio
   e) Use calculator add, divide, multiply to calculate percentage shares
   f) Present: both star counts, difference, ratio, percentage shares (should total 100%)

5. TRENDING TOPIC SCOUT (topic)
   Purpose: Analyse trending topic spread and momentum
   Required steps:
   a) Call searchRepositories for topic, sorted by stars
   b) Identify top result and bottom result star counts
   c) Use calculator subtract: top - bottom for spread
   d) Use calculator add: top + bottom, then divide by 2 for midpoint
   e) Use temperature converter: celsius_to_fahrenheit for momentum temperature
   f) Present: top repo, bottom repo, spread, midpoint, temperature in °F

EVALUATION CRITERIA:

1. Step Completion (40 points):
   - All required API calls made
   - All required calculator operations performed
   - All required temperature conversions done
   - No critical steps skipped

2. Step Sequence (20 points):
   - Steps executed in logical order
   - Data gathered before calculations
   - Calculations done before presentation

3. Tool Selection (20 points):
   - Correct tools used for each step
   - No unnecessary tool calls
   - Efficient execution

4. Output Completeness (20 points):
   - All required metrics presented
   - Correct units (°C or °F as specified)
   - Clear, structured presentation

SCORING:
5 = Perfect (90-100 points): All steps completed in correct order, efficient execution
4 = Good (70-89 points): All steps done, minor sequence issues or one extra tool call
3 = Acceptable (50-69 points): Core steps completed but missing optional step or inefficient
2 = Incomplete (30-49 points): Missing critical steps or wrong sequence
1 = Failed (0-29 points): Did not follow workflow, skipped multiple steps

ANALYSIS FORMAT:
1. Identify which skill was executed
2. List steps that WERE completed
3. List steps that WERE MISSING
4. Assess step sequence and efficiency
5. Provide final score with reasoning

Provide your score (1-5) and detailed analysis."""
