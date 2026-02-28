# Infrastructure Testing Guide

Automated infrastructure tests using pytest that interact with live AWS services.

## Quick Reference

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-infrastructure` | Run all infrastructure tests |
| `make test-memory` | Run memory infrastructure tests |
| `make test-memory-quick` | Skip slow tests (faster development) |
| `make test-gateways` | Run gateway infrastructure tests |
| `make test-gateways-quick` | Skip slow gateway tests |
| `make test-runtimes` | Run runtime infrastructure tests |
| `make test-runtimes-quick` | Skip slow runtime tests |

## Test Categories

### Memory Infrastructure Tests

### Running Tests

```bash
# All memory tests
make test-memory

# Skip slow tests (60-90s waits)
make test-memory-quick

# Using pytest directly
pytest tests/infrastructure/memory/ -v

# Specific test file
pytest tests/infrastructure/memory/test_memory_create.py -v
```

### Test Files

- **`test_memory_create.py`** - Create memory events (preferences, facts, summaries)
- **`test_memory_queries.py`** - Search and query memory records
- **`test_memory_view.py`** - List and view stored memories

### Important: Memory Extraction Delay

Memory extraction is **asynchronous (60-90 seconds)**. After creating test events, wait before verifying:

```bash
# 1. Create test events
pytest tests/infrastructure/memory/test_memory_create.py -v

# 2. Wait for extraction
sleep 90

# 3. Verify records exist
pytest tests/infrastructure/memory/test_memory_view.py -v
```

### Test Isolation

- All tests use `test-user` as actor ID (isolated from real users)
- Unique session IDs prevent test interference
- Tests don't auto-cleanup (manual deletion via AWS console if needed)

### Shared Fixtures

Defined in `tests/infrastructure/memory/conftest.py`:

- `test_actor_id` - Returns `"test-user"`
- `memory_id` - Retrieved from SSM Parameter Store
- `unique_session_id` - UUID-based session ID (per test)
- `bedrock_agentcore_client` - Boto3 client for AgentCore

## Pytest Markers

Configure in `pytest.ini`:

- `@pytest.mark.infrastructure` - Requires AWS services
- `@pytest.mark.slow` - Long-running tests (> 60 seconds)

```bash
# Run only infrastructure tests
pytest -m infrastructure

# Skip slow tests
pytest -m "infrastructure and not slow"
```

## Prerequisites

1. Complete setup from main README up to `make deploy`
2. Deployed stack with memory configured
3. Valid AWS credentials
4. Python virtual environment activated

## Auto-Skipping

Tests automatically skip if:
- Stack not deployed (memory ID not found in SSM)
- No records exist for `test-user`
- Prerequisites missing

## Troubleshooting

**"Memory ID not found"**
```bash
make deploy
```

**"No records found for test-user"**
```bash
# Create test data
pytest tests/infrastructure/memory/test_memory_create.py -v
sleep 90
```

### Gateway Infrastructure Tests

Tests for AgentCore gateway authentication and tool invocation.

#### Running Tests

```bash
# All gateway tests
make test-gateways

# Skip slow tests
make test-gateways-quick

# Using pytest directly
pytest tests/infrastructure/gateways/ -v
```

#### Test Files

- **`test_iam_auth.py`** - IAM gateway SigV4 authentication validation
- **`test_jwt_auth.py`** - JWT gateway OAuth2 token handling and refresh
- **`test_tool_invocation.py`** - End-to-end tool invocation (calculator, temperature converter)
- **`test_error_handling.py`** - Error scenarios (invalid tools, malformed arguments)

#### What's Tested

**Authentication:**
- SigV4 signing works correctly (IAM gateway)
- OAuth2 token acquisition and caching (JWT gateway)
- Requests succeed with valid credentials

**Tool Invocation:**
- List tools returns expected structure
- Search tools finds relevant results
- Invoke tools returns correct responses

**Error Handling:**
- Invalid tool names return errors
- Malformed arguments are rejected
- Invalid methods return appropriate errors

### Runtime Infrastructure Tests

Tests for AgentCore runtime invocation and basic performance.

#### Running Tests

```bash
# All runtime tests
make test-runtimes

# Skip slow tests (performance benchmarks)
make test-runtimes-quick

# Using pytest directly
pytest tests/infrastructure/runtimes/ -v
```

#### Test Files

- **`test_agent_invocation.py`** - Agent runtime end-to-end orchestration
- **`test_mcp_invocation.py`** - MCP runtime direct invocation
- **`test_performance.py`** - Basic response time measurements (marked as slow)

#### What's Tested

**Agent Runtime:**
- Agent invocation with prompts
- Tool usage (calculations)
- Structured response format
- Session and actor ID handling

**MCP Runtime:**
- Direct tool invocation
- List tools functionality
- Correct operation results

**Performance (Informational):**
- Agent response time (< 30s)
- MCP runtime response time (< 5s)

**Note:** Performance tests are informational, not strict benchmarks.

## Best Practices

1. **Organise by feature** - Group related tests in subdirectories
2. **Use fixtures** - Share common setup via `conftest.py` files
3. **Mark tests** - Use `@pytest.mark.infrastructure` and `@pytest.mark.slow`
4. **Test isolation** - Use unique IDs (e.g., `test-user`, unique session IDs)
5. **Document prerequisites** - Clear requirements in README files
6. **Skip gracefully** - Skip tests when prerequisites aren't met
