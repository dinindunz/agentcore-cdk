"""Math Accuracy Evaluator

Validates calculator tool calls for mathematical correctness.
Ensures operations (add, subtract, multiply, divide) produce accurate results
with appropriate precision.
"""

# Evaluator configuration
EVALUATOR_NAME = "MathAccuracy"
EVALUATION_LEVEL = "toolCall"  # Evaluate each tool call individually

# Model configuration
MODEL_ID = "anthropic.claude-sonnet-4-5-v3:0"  # Balanced performance
TEMPERATURE = 0.0  # Deterministic for consistent math validation
TOP_P = 0.95
MAX_TOKENS = 512  # Short explanations needed

# Scoring schema
SCORING_TYPE = "numbered_scale"
MIN_VALUE = 1
MAX_VALUE = 5
SCORING_DESCRIPTION = "1=Completely wrong, 5=Perfect accuracy"

# Description
DESCRIPTION = "Validates mathematical correctness of calculator operations"

# Evaluation prompt
PROMPT = """You are evaluating calculator tool calls for mathematical accuracy.

TOOL CALL CONTEXT:
- Tool name: {tool_name}
- Tool input: {tool_input}
- Tool output: {tool_output}

EVALUATION CRITERIA:

1. Mathematical Correctness: Verify the calculation is accurate
   - Addition: Check sum is correct
   - Subtraction: Check difference is correct
   - Multiplication: Check product is correct
   - Division: Check quotient is correct (watch for division by zero)

2. Precision: Ensure appropriate decimal places
   - Standard operations: At least 2 decimal places
   - Division: At least 3 decimal places for fractions
   - Example: 10 ÷ 3 should be 3.333..., not 3.3

3. Edge Cases:
   - Division by zero should return error or infinity
   - Negative numbers handled correctly
   - Very large/small numbers use scientific notation if needed

4. Common Errors to Detect:
   - Wrong operation used (e.g., added instead of multiplied)
   - Rounding errors (3.33 vs 3.333)
   - Missing decimal precision
   - Incorrect handling of negative numbers

SCORING:
5 = Perfect: Mathematically correct with appropriate precision
4 = Minor precision issue: Correct but could have more decimal places (e.g., 3.33 vs 3.333)
3 = Rounding error: Correct approach but noticeable rounding (e.g., 3.3 vs 3.333)
2 = Wrong operation: Used add instead of multiply, subtract instead of divide, etc.
1 = Completely wrong: Incorrect result or major calculation error

IMPORTANT:
- Verify the actual math by performing the calculation yourself
- Don't just check if the result "looks reasonable" - validate exact accuracy
- Be strict about precision for division operations

Provide your score (1-5) and a brief explanation of your reasoning."""
