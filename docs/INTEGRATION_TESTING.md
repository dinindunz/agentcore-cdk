# Integration Testing Guide

Automated integration tests using pytest that interact with live AWS services.

## Quick Reference

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-integration` | Run all integration tests |
| `make test-memory` | Run memory integration tests |
| `make test-memory-quick` | Skip slow tests (faster development) |

## Memory Integration Tests

### Running Tests

```bash
# All memory tests
make test-memory

# Skip slow tests (60-90s waits)
make test-memory-quick

# Using pytest directly
pytest tests/integration/memory/ -v

# Specific test file
pytest tests/integration/memory/test_memory_create.py -v
```

### Test Files

- **`test_memory_create.py`** - Create memory events (preferences, facts, summaries)
- **`test_memory_queries.py`** - Search and query memory records
- **`test_memory_view.py`** - List and view stored memories

### Important: Memory Extraction Delay

Memory extraction is **asynchronous (60-90 seconds)**. After creating test events, wait before verifying:

```bash
# 1. Create test events
pytest tests/integration/memory/test_memory_create.py -v

# 2. Wait for extraction
sleep 90

# 3. Verify records exist
pytest tests/integration/memory/test_memory_view.py -v
```

### Test Isolation

- All tests use `test-user` as actor ID (isolated from real users)
- Unique session IDs prevent test interference
- Tests don't auto-cleanup (manual deletion via AWS console if needed)

### Shared Fixtures

Defined in `tests/integration/memory/conftest.py`:

- `test_actor_id` - Returns `"test-user"`
- `memory_id` - Retrieved from SSM Parameter Store
- `unique_session_id` - UUID-based session ID (per test)
- `bedrock_agentcore_client` - Boto3 client for AgentCore

## Pytest Markers

Configure in `pytest.ini`:

- `@pytest.mark.integration` - Requires AWS services
- `@pytest.mark.slow` - Long-running tests (> 60 seconds)

```bash
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "integration and not slow"
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
pytest tests/integration/memory/test_memory_create.py -v
sleep 90
```

## Best Practices

1. **Organise by feature** - Group related tests in subdirectories
2. **Use fixtures** - Share common setup via `conftest.py` files
3. **Mark tests** - Use `@pytest.mark.integration` and `@pytest.mark.slow`
4. **Test isolation** - Use unique IDs (e.g., `test-user`, unique session IDs)
5. **Document prerequisites** - Clear requirements in README files
6. **Skip gracefully** - Skip tests when prerequisites aren't met
