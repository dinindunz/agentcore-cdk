# Manual Testing Guide

Manual test scripts for exploring and validating AgentCore components.

## Quick Reference

| Command | Description |
|---------|-------------|
| `make agent-chat` | Interactive chat with agent |
| `make skill-tests` | Run all agent skill tests |
| `make iam-tests` | Run all IAM gateway tests |
| `make jwt-tests` | Run all JWT gateway tests |
| `make view-memory` | View memory for actor (from `.env`) |
| `make eval-list` | List evaluation configurations |

## Agent Runtime

### Interactive Chat
```bash
make agent-chat                    # Start interactive chat session
```

Set `ACTOR_ID` in `.env` to maintain identity across sessions for long-term memory.

### Skill Tests

```bash
make skill-issue-heat-map          # Issue heat map analysis
make skill-portfolio-summary       # Portfolio summary with stats
make skill-repo-comparison         # Compare repositories
make skill-repo-hotness            # Rate repository activity
make skill-trending-topic          # Discover trending topics
```

**Location:** `tests/manual/runtimes/agent/skill_tests/`

## Gateway Testing

### IAM Gateway (SigV4 Auth)

```bash
make iam-list-tools                # List all available tools
make iam-search-tools              # Semantic tool search
make iam-test-calculator           # Test calculator MCP
make iam-test-skill-search         # Test skill search MCP
make iam-mcp-tests                 # Run all IAM MCP tests

# Generic tool invocation
make iam-invoke-tool TOOL=calculator___add ARGS='{"a": 5, "b": 3}'
```

**Location:** `tests/manual/gateways/iam/`

### JWT Gateway (Cognito OAuth2)

```bash
make jwt-list-tools                # List all available tools
make jwt-search-tools              # Semantic tool search
make jwt-test-github               # Test GitHub MCP
make jwt-test-temperature          # Test temperature converter MCP
make jwt-mcp-tests                 # Run all JWT MCP tests

# Generic tool invocation
make jwt-invoke-tool TOOL=temperature-converter___celsius_to_fahrenheit ARGS='{"celsius": 25}'
```

**Location:** `tests/manual/gateways/jwt/`

## MCP Runtime

Direct MCP runtime invocation (bypassing gateway):

```bash
make mcp-invoke-calculator         # Test calculator runtime directly
```

**Location:** `tests/manual/runtimes/mcp/`

## Memory

```bash
make view-memory                   # View memory for actor from .env

# Custom actor ID
python tests/manual/memory/view_memory.py your-actor-id
```

Shows preference, semantic, and summary memory records.

**Location:** `tests/manual/memory/`

## Evaluations

```bash
make eval-list                     # List online evaluation configs
make eval-results                  # Query results (last 1 hour)
make eval-results HOURS=24         # Query results (custom timeframe)
```

**Location:** `tests/manual/evaluations/`

## Configuration

All manual tests require:
- `.env` file with `REGION_NAME`, `AWS_ACCOUNT_ID`, `ENV`, `GITHUB_TOKEN`
- Deployed stack (`make deploy`)
- Valid AWS credentials

SSM parameters and secrets are auto-fetched by test scripts.

## Running Custom Commands

All test scripts can be run directly:

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run any script directly
cd tests/manual/gateways/jwt
python list_tools.py
```

See individual README files in test directories for script-specific details.
