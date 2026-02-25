"""Temperature Conversion Accuracy Evaluator

Validates temperature conversion tool calls use correct formulas.
Critical for GitHub analysis skills that use temperature as a metaphor
for metrics (hotness, burden, momentum, etc.).
"""

# Evaluator configuration
EVALUATOR_NAME = "TemperatureConversionAccuracy"
EVALUATION_LEVEL = "toolCall"  # Evaluate each conversion

# Model configuration
MODEL_ID = "anthropic.claude-haiku-4-5-v1:0"  # Fast model for simple formula validation
TEMPERATURE = 0.0  # Deterministic
TOP_P = 0.9
MAX_TOKENS = 256  # Very short explanations

# Scoring schema
SCORING_TYPE = "binary"
SCORING_DESCRIPTION = "Yes if conversion is accurate, No if any error"

# Description
DESCRIPTION = "Validates temperature conversion formula correctness"

# Evaluation prompt
PROMPT = """You are evaluating temperature conversion tool calls for formula accuracy.

TOOL CALL CONTEXT:
- Tool name: {tool_name}
- Tool input: {tool_input}
- Tool output: {tool_output}

CONVERSION FORMULAS:

1. Celsius to Fahrenheit: °F = (°C × 9/5) + 32
   - Example: 0°C = 32°F
   - Example: 100°C = 212°F
   - Example: 25°C = 77°F
   - Example: -40°C = -40°F

2. Fahrenheit to Celsius: °C = (°F - 32) × 5/9
   - Example: 32°F = 0°C
   - Example: 212°F = 100°C
   - Example: 77°F = 25°C
   - Example: -40°F = -40°C

VALIDATION PROCESS:
1. Identify which conversion is being performed (C→F or F→C)
2. Extract the input value and output value
3. Apply the correct formula yourself
4. Compare your result with the tool output
5. Check precision (at least 2 decimal places for non-integer results)

COMMON ERRORS TO DETECT:
- Using wrong formula (adding 32 for F→C instead of subtracting)
- Wrong conversion factor (using 5/9 for C→F or 9/5 for F→C)
- Order of operations error (multiplying before adding/subtracting)
- Insufficient precision (77 instead of 77.0 or 77.00)
- Rounding too aggressively (25.5 → 25 instead of keeping decimal)

SCORING:
Yes = Conversion is mathematically correct within 0.01 degrees
No = Any mathematical error, wrong formula, or precision < 2 decimal places

IMPORTANT:
- Perform the calculation yourself to verify
- Accept answers within 0.01 degrees (to account for floating point)
- Reject answers with < 2 decimal places unless result is a whole number

Provide Yes/No and a brief explanation."""
