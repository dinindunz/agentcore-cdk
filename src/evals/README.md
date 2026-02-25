# Custom Evaluator Definitions

This directory contains custom evaluator configurations for domain-specific validation of the AgentCore agent.

## Directory Structure

```
src/evals/
├── math_accuracy.py               # Calculator operation validation
├── temperature_conversion.py      # Temperature formula validation
├── skill_workflow.py              # Skill completeness checking
├── github_integrity.py            # Data hallucination detection
└── output_format.py               # Output format validation
```

## Evaluator Architecture

Each evaluator module defines configuration constants that are imported by the CDK stack:

```python
# Evaluator configuration
EVALUATOR_NAME = "EvaluatorName"           # Name (converted to snake_case)
EVALUATION_LEVEL = "trace"                 # "session", "trace", or "toolCall"

# Model configuration
MODEL_ID = "anthropic.claude-sonnet-4-5-v3:0"
TEMPERATURE = 0.0
TOP_P = 0.95
MAX_TOKENS = 1024

# Scoring schema
SCORING_TYPE = "numbered_scale"            # or "binary"
MIN_VALUE = 1                              # For numbered_scale
MAX_VALUE = 5                              # For numbered_scale
SCORING_DESCRIPTION = "1=Poor, 5=Excellent"

# Description and prompt
DESCRIPTION = "What this evaluator measures"
PROMPT = """Evaluation instructions..."""
```

## Custom Evaluators

### 1. Math Accuracy (`math_accuracy.py`)
- **Level**: Tool call
- **Purpose**: Validates calculator operations (add, subtract, multiply, divide)
- **Model**: Claude Sonnet 3.5
- **Scoring**: 5-point scale (1=wrong, 5=perfect)
- **Temperature**: 0.0 (deterministic)

### 2. Temperature Conversion (`temperature_conversion.py`)
- **Level**: Tool call
- **Purpose**: Validates C↔F conversion formulas
- **Model**: Claude Sonnet 3.5
- **Scoring**: Binary (Yes/No)
- **Temperature**: 0.0 (deterministic)

### 3. Skill Workflow (`skill_workflow.py`)
- **Level**: Trace
- **Purpose**: Checks if all skill steps were completed
- **Model**: Claude Sonnet 3.5
- **Scoring**: 5-point scale (1=failed, 5=perfect)
- **Temperature**: 0.1 (slight variation for nuanced judgment)

### 4. GitHub Integrity (`github_integrity.py`)
- **Level**: Trace
- **Purpose**: Detects hallucinated GitHub data (repos, stars, counts)
- **Model**: Claude Sonnet 3.5
- **Scoring**: 5-point scale (1=major hallucination, 5=perfect)
- **Temperature**: 0.0 (strict fact-checking)

### 5. Output Format (`output_format.py`)
- **Level**: Trace
- **Purpose**: Validates response contains required fields with proper units
- **Model**: Claude Sonnet 3.5
- **Scoring**: Binary (Yes/No)
- **Temperature**: 0.0 (deterministic)

## Built-in Evaluators

The stack uses 5 built-in AWS evaluators alongside the 5 custom evaluators (10 total):

1. **Builtin.Helpfulness** — Assesses whether the agent's response is helpful to the user
2. **Builtin.Correctness** — Evaluates factual accuracy and correctness of the response
3. **Builtin.ToolSelectionAccuracy** — Validates the agent selected appropriate tools for the task
4. **Builtin.ToolParameterAccuracy** — Checks if tool parameters are correct for the intent
5. **Builtin.ResponseRelevance** — Measures how relevant the response is to the user's query

Built-in evaluators use AWS-managed models and prompts (not configurable). They provide general quality assessment that complements the domain-specific validation from custom evaluators.

## Adding a New Custom Evaluator

### Step 1: Create the evaluator definition file

```python
# src/evals/new_evaluator.py
"""New Evaluator Description."""

EVALUATOR_NAME = "NewEvaluator"
EVALUATION_LEVEL = "trace"  # or "session" or "toolCall"

# Model configuration
MODEL_ID = "anthropic.claude-sonnet-4-5-v3:0"
TEMPERATURE = 0.0
TOP_P = 0.95
MAX_TOKENS = 1024

# Scoring schema
SCORING_TYPE = "numbered_scale"  # or "binary"
MIN_VALUE = 1
MAX_VALUE = 5
SCORING_DESCRIPTION = "Scoring description"

DESCRIPTION = "What this evaluator measures"

PROMPT = """Your evaluation prompt here.

Include:
- What to evaluate
- Criteria
- Scoring guidance
- Examples
"""
```

### Step 2: Export in `__init__.py`

```python
# src/evals/__init__.py
from . import (
    # ... existing evaluators
    new_evaluator,
)

__all__ = [
    # ... existing evaluators
    "new_evaluator",
]

EVALUATORS = {
    # ... existing evaluators
    "new_evaluator": new_evaluator,
}
```

### Step 3: Add to AgentCore stack

```python
# src/cdk/stacks/agentcore.py

# Import
from ...evals import (
    # ... existing imports
    new_evaluator,
)

# Create custom evaluator
new_eval = CustomEvaluatorConstruct(
    self,
    "NewEvaluator",
    evaluator_name=new_evaluator.EVALUATOR_NAME,
    evaluation_level=new_evaluator.EVALUATION_LEVEL,
    prompt=new_evaluator.PROMPT,
    scoring_schema=(
        ScoringSchemaDefinition.numbered_scale(
            min_value=new_evaluator.MIN_VALUE,
            max_value=new_evaluator.MAX_VALUE,
            description=new_evaluator.SCORING_DESCRIPTION,
        )
        if new_evaluator.SCORING_TYPE == "numbered_scale"
        else ScoringSchemaDefinition.binary(
            description=new_evaluator.SCORING_DESCRIPTION
        )
    ),
    model_config=ModelConfiguration(
        model_id=new_evaluator.MODEL_ID,
        temperature=new_evaluator.TEMPERATURE,
        top_p=new_evaluator.TOP_P,
        max_tokens=new_evaluator.MAX_TOKENS,
    ),
    description=new_evaluator.DESCRIPTION,
)

# Add to online evaluation
agent_eval = OnlineEvaluationConstruct(
    # ...
    evaluators=[
        # ... built-in and other custom evaluators
        new_eval.to_evaluator_reference(),
    ],
)
```

## Built-in vs Custom Evaluators

| Feature | Built-in Evaluators | Custom Evaluators |
|---------|-------------------|-------------------|
| **Setup** | Ready to use (`Builtin.Helpfulness`) | Must be created |
| **Model** | Pre-selected by AWS (not disclosed) | Your choice (Claude Opus, Sonnet, Haiku, etc.) |
| **Prompt** | Fixed, optimised by AWS | Fully customisable |
| **Scoring** | Predefined scales | Custom scales (numbered or binary) |
| **Temperature** | Fixed | Configurable (0.0-1.0) |
| **Inference Config** | Fixed | Configurable (top_p, max_tokens, stop sequences) |
| **Use Case** | General quality metrics | Domain-specific validation |

### When to Use Custom Evaluators

Use custom evaluators when:
- ✅ You need **deterministic validation** (exact math, format checks)
- ✅ Built-in evaluators miss **domain-specific quality issues**
- ✅ You want **specific model choice** (e.g., Opus for complex reasoning)
- ✅ You need **custom scoring criteria** for your use case
- ✅ You want to validate **business-specific requirements**

## Model Selection Guide

| Model | Use Case | Cost | Speed | When to Use |
|-------|----------|------|-------|-------------|
| **Opus 4.6** | Complex reasoning | Highest | Slowest | Workflow analysis, multi-step validation, nuanced judgment |
| **Sonnet 4.5** | General evaluation | Medium | Medium | Most evaluations, balanced quality/speed |
| **Haiku 4.5** | Simple validation | Lowest | Fastest | Binary checks, format validation, simple rules |

## Temperature Guidelines

| Temperature | Use Case | Consistency |
|-------------|----------|-------------|
| **0.0** | Math, facts, deterministic validation | Highest (recommended) |
| **0.1-0.3** | Nuanced judgment, workflow assessment | High |
| **0.5+** | Not recommended for evaluation | Low |

## Scoring Schema Guidelines

### Numbered Scale
Best for: Graduated quality assessment, nuanced evaluation
```python
SCORING_TYPE = "numbered_scale"
MIN_VALUE = 1
MAX_VALUE = 5
SCORING_DESCRIPTION = "1=Poor, 2=Fair, 3=Good, 4=Very Good, 5=Excellent"
```

### Binary
Best for: Pass/fail checks, deterministic validation
```python
SCORING_TYPE = "binary"
SCORING_DESCRIPTION = "Yes if correct, No if error"
```

## Evaluation Levels

### Session Level (`"session"`)
- Evaluates full conversation sessions
- Access to all turns and context
- Good for: Goal completion, overall success

### Trace Level (`"trace"`)
- Evaluates single user-agent interaction
- Access to: input, output, tool calls
- Good for: Response quality, workflow, format

### Tool Call Level (`"toolCall"`)
- Evaluates individual tool invocations
- Access to: tool name, input, output
- Good for: Tool accuracy, parameter validation

## Best Practices

### 1. Clear, Specific Prompts
✅ Define exact criteria with examples
✅ Include scoring guidance
✅ Show edge cases
❌ Avoid vague instructions

### 2. Appropriate Temperature
✅ 0.0 for math/facts
✅ 0.1-0.3 for judgment
❌ Never > 0.5 for evaluation

### 3. Right Model for Task
✅ Haiku for simple checks
✅ Sonnet for general eval
✅ Opus for complex reasoning
❌ Don't waste Opus on format checks

### 4. Efficient Token Usage
✅ Shorter prompts for binary checks (256 tokens)
✅ Medium for general eval (512-1024 tokens)
✅ Longer for complex analysis (2048+ tokens)
❌ Don't over-allocate

## Testing Evaluators

After deploying:

```bash
# Deploy stack with evaluators
make deploy

# Trigger evaluations by using agent
make agent-chat

# View evaluation results
make eval-results

# List evaluation configurations
make eval-list
```
